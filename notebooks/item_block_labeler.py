import marimo

__generated_with = "0.25.1"
app = marimo.App(width="full")


@app.cell
def imports():
    from pathlib import Path

    import marimo as mo
    import matplotlib.pyplot as plt
    import numpy as np
    from PIL import Image

    from vox_paginae.blocks import (
        add_block,
        block_labels,
        clear_balance,
        close_deed_record,
        crop,
        deed_boxes,
        deed_choices,
        deed_path,
        delete_block,
        find_books,
        list_pages,
        load_deed_records,
        load_deeds,
        move_deed_record,
        new_deed_record,
        next_page,
        replace_balance,
        replace_block,
        resume,
        save_deed_record,
        saved_boxes,
        set_balance,
        set_header,
        single_overledene,
        split_label,
        thumbnail,
    )

    return (
        Image,
        Path,
        add_block,
        block_labels,
        clear_balance,
        close_deed_record,
        crop,
        deed_boxes,
        deed_choices,
        deed_path,
        delete_block,
        find_books,
        list_pages,
        load_deed_records,
        load_deeds,
        mo,
        move_deed_record,
        new_deed_record,
        next_page,
        np,
        plt,
        replace_balance,
        replace_block,
        resume,
        save_deed_record,
        saved_boxes,
        set_balance,
        set_header,
        single_overledene,
        split_label,
        thumbnail,
    )


@app.cell
def _(Path, mo):
    # `marimo edit|run notebooks/item_block_labeler.py -- --data-root <dir>` overrides the default.
    default_root = Path(
        mo.cli_args().get("data-root")
        or Path.home()
    )
    root_picker = mo.ui.file_browser(
        initial_path=default_root,
        selection_mode="directory",
        multiple=False,
    )
    return default_root, root_picker


@app.cell(hide_code=True)
def _(default_root, mo, root_picker):
    root = root_picker.path() or default_root
    mo.accordion({f"root: {root} (click to change)": root_picker})
    return (root,)


@app.cell(hide_code=True)
def annotator_state(mo):
    # (name, locked). Its own cell: the cells below rebuild from it on lock and unlock.
    get_annotator, set_annotator = mo.state(("", False))
    return get_annotator, set_annotator


@app.cell(hide_code=True)
def annotator_input(get_annotator, mo):
    _name, _locked = get_annotator()
    # Read-only while locked: a stray keystroke cannot change who is recorded.
    # debounce: lock enables while typing, as save does
    annotator_in = mo.ui.text(
        label="annotator", value=_name, disabled=_locked, debounce=300
    )
    # A plain name for now: every write records it. "" until locked: nothing past the
    # book cell runs. From the state, not the input, so typing reruns nothing below.
    annotator_name = _name if _locked else ""
    return annotator_in, annotator_name


@app.cell(hide_code=True)
def annotator_lock(annotator_in, get_annotator, mo, set_annotator):
    _name, _locked = get_annotator()
    lock_btn = mo.ui.button(
        label="unlock" if _locked else "lock",
        disabled=not (_locked or annotator_in.value.strip()),
        on_click=lambda _: set_annotator(
            (_name, False) if _locked else (annotator_in.value.strip(), True)
        ),
    )
    annotator_row = mo.hstack([annotator_in, lock_btn], justify="start", align="end")
    return (annotator_row,)


@app.cell(hide_code=True)
def session_state(find_books, list_pages, mo, resume, root):
    books = find_books(root)
    book_pages = [list_pages(b) for b in books]
    # Everything below resets when the root changes.
    get_book_page, set_book_page = mo.state(
        resume(books)
    )  # (book index, page index)
    # None = no deed/person open: one is opened from the deed row. Resume never reopens
    # one, so this always starts as None.
    get_deed_record, set_deed_record = mo.state(None)
    # deed_id of the open (or last closed) deed/person: the debug pane shows its file.
    get_deed_id, set_deed_id = mo.state(None)
    get_pending_boxes, set_pending_boxes = mo.state(
        []
    )  # (scan, bbox) boxes of the block being drawn
    # Label ("A2") of the block loaded by edit: save replaces it. None = save adds a block.
    get_editing, set_editing = mo.state(None)
    # Type to prefill the radio with. Set only on edit and close, so a save keeps the last
    # type used without rebuilding the radio.
    get_type, set_type = mo.state(None)
    # True while the open deed/person's header is redrawn: the rest of the form is
    # locked. Self loops: the header buttons cell both reads and sets it.
    get_editing_header, set_editing_header = mo.state(
        False, allow_self_loops=True
    )
    # Likewise while the saved balance is edited; the balance buttons cell reads and sets it.
    get_editing_balance, set_editing_balance = mo.state(
        False, allow_self_loops=True
    )
    return (
        book_pages,
        books,
        get_book_page,
        get_deed_id,
        get_deed_record,
        get_editing,
        get_editing_balance,
        get_editing_header,
        get_pending_boxes,
        get_type,
        set_book_page,
        set_deed_id,
        set_deed_record,
        set_editing,
        set_editing_balance,
        set_editing_header,
        set_pending_boxes,
        set_type,
    )


@app.cell(hide_code=True)
def page_buttons(
    annotator_name,
    book,
    book_pages,
    close_deed_record,
    get_deed_record,
    get_editing,
    get_editing_balance,
    get_editing_header,
    get_pending_boxes,
    mo,
    next_page,
    page,
    page_i,
    pages,
    save_deed_record,
    set_book_page,
    set_deed_record,
    set_type,
):
    _last_page = page_i == len(pages) - 1

    def _next_page(_):
        if (
            _last_page
        ):  # a deed/person never crosses books: close the open one, if any
            if get_deed_record() is not None:
                _path = save_deed_record(
                    book,
                    close_deed_record(
                        get_deed_record(), [p.name for p in pages], page.name
                    ),
                    annotator_name,
                )
                mo.status.toast(f"saved {_path.name}, deed/person closed")
            set_deed_record(None)
            set_type(None)
        set_book_page(
            lambda book_page: next_page(
                book_page, [len(p) for p in book_pages]
            )
        )

    next_page_btn = mo.ui.button(
        label="next page",
        # On the last page it closes the open deed/person: same rules as close deed/person.
        disabled=_last_page
        and (
            bool(get_pending_boxes())
            or get_editing() is not None
            or get_editing_header()
            or get_editing_balance()
        ),
        on_click=_next_page,
    )
    # Stays inside the current book: a deed/person never crosses books.
    prev_page_btn = mo.ui.button(
        label="prev page",
        disabled=page_i == 0,
        on_click=lambda _: set_book_page(
            lambda book_page: (book_page[0], max(book_page[1] - 1, 0))
        ),
    )
    return next_page_btn, prev_page_btn


@app.cell(hide_code=True)
def type_input(get_type, mo):
    type_radio = mo.ui.radio(
        options=["assets", "liabilities"], value=get_type(), inline=True
    )
    return (type_radio,)


@app.cell(hide_code=True)
def _(block_labels, get_deed_record, get_editing, mo):
    get_deed_record()  # re-created (cleared) after every open, write and close
    # Prefilled from the block being edited, if any.
    _item = dict(block_labels(get_deed_record())).get(get_editing(), {})
    category_in = mo.ui.text(
        label="category", value=_item.get("category") or ""
    )
    # debounce: save enables while typing, as for the name
    value_in = mo.ui.text(
        label="value", value=_item.get("amount", ""), debounce=300
    )
    desc_in = mo.ui.text(
        label="description",
        value=_item.get("description", ""),
        full_width=True,
        debounce=300,
    )
    return category_in, desc_in, value_in


@app.cell(hide_code=True)
def _(
    annotator_name,
    annotator_row,
    book_dd,
    book_pages,
    books,
    get_book_page,
    load_deeds,
    mo,
    root,
):
    # The locked name comes first: nothing past here runs without it.
    mo.stop(
        not annotator_name,
        mo.vstack(
            [annotator_row, mo.md("**give your name and lock it to start**")]
        ),
    )
    book_i, page_i = get_book_page()
    # Each stop keeps the book dropdown: leaving a book never needs the jump slider.
    mo.stop(
        book_i >= len(books),
        mo.vstack([annotator_row, book_dd, mo.md("**all books done**")]),
    )
    book = books[book_i]
    # Every book has one: a missing deeds.json is a data mistake, so nothing past here runs.
    deeds = load_deeds(book)
    mo.stop(
        deeds is None,
        mo.vstack(
            [
                annotator_row,
                book_dd,
                mo.md(f"**no `deeds.json` in book `{book.relative_to(root)}`**"),
            ]
        ),
    )
    pages = book_pages[book_i]
    page = pages[page_i]
    return book, deeds, page, page_i, pages


@app.cell(hide_code=True)
def view_sliders(mo):
    # The page is shown FIG_H * 100 px tall; quality = PNG pixels per inch of FIG_H, so
    # 100 is 1:1 with the screen and higher is sharper (on HiDPI screens) but slower.
    QUALITY_DPI = [100, 150, 200, 300]
    quality_slider = mo.ui.slider(
        steps=QUALITY_DPI, value=150, label="quality"
    )
    fig_h_slider = mo.ui.slider(4.0, 14.0, step=0.5, value=8.0, label="height")
    return fig_h_slider, quality_slider


@app.cell(hide_code=True)
def _(Image, fig_h_slider, np, page, quality_slider):
    # Decode at reduced scale (fast), then Lanczos down to exactly the PNG height (sharp).
    # page_size keeps bboxes in original pixels.
    # The PNG goes out in the layout cell's output, which marimo caps (output_max_bytes in
    # pyproject.toml; over it, the whole form is replaced by an error). Measured ~1.1 bytes
    # per pixel on these scans, so PNG pixels are capped and past that the quality slider
    # stops adding any.
    MAX_PNG_PX = 5_000_000
    _im = Image.open(page)
    page_size = _im.size
    _fig_area = (
        fig_h_slider.value**2 * page_size[0] / page_size[1]
    )  # square inches
    png_dpi = min(quality_slider.value, (MAX_PNG_PX / _fig_area) ** 0.5)
    _px = round(fig_h_slider.value * png_dpi)
    _im.draft("L", (1, _px))
    _im.thumbnail((page_size[0], _px), Image.LANCZOS)
    page_img = np.asarray(_im)
    return page_img, page_size, png_dpi


@app.cell(hide_code=True, expand_output=True)
def _(
    book,
    deed_boxes,
    fig_h_slider,
    get_deed_id,
    get_deed_record,
    get_pending_boxes,
    mo,
    page,
    page_img,
    page_size,
    plt,
    png_dpi,
    saved_boxes,
):
    FIG_H = fig_h_slider.value  # inches, shown at 100 px each
    DPI = png_dpi  # quality, unless capped
    # By label initial: header, balance, asset, liability.
    TYPE_COLOURS = {
        "H": "tab:green",
        "B": "tab:purple",
        "A": "tab:blue",
        "L": "tab:orange",
    }

    _w, _h = page_size
    # Figure matches the page aspect and axes fill it; otherwise mo.ui.matplotlib maps
    # the pointer across the whole canvas and every box comes back offset.
    _fig, _ax = plt.subplots(figsize=(FIG_H * _w / _h, FIG_H), dpi=DPI)
    _fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    _ax.imshow(
        page_img,
        extent=(0, _w, _h, 0),
        cmap="gray",
        vmin=0,  # fixed uint8 range: no contrast stretch, flat pages not black
        vmax=255,
    )
    _ax.set_xlim(0, _w)
    _ax.set_ylim(_h, 0)
    _ax.set_axis_off()

    def _draw(bbox, colour, label=None, style="-", alpha=1.0):
        _x0, _y0, _x1, _y1 = bbox
        _ax.add_patch(
            plt.Rectangle(
                (_x0, _y0),
                _x1 - _x0,
                _y1 - _y0,
                fill=False,
                edgecolor=colour,
                linewidth=2,
                linestyle=style,
                alpha=alpha,
            )
        )
        if label:
            _ax.text(
                _x0,
                _y0,
                label,
                color=colour,
                va="bottom",
                fontsize=14,
                fontweight="bold",
            )

    # Saved boxes of other persons (and of a closed one), faded: shared pages, restarts.
    _editing = get_deed_id() if get_deed_record() is not None else None
    for _label, _bbox in saved_boxes(book, page.name, _editing):
        _draw(_bbox, TYPE_COLOURS[_label[0]], alpha=0.4)
    for _label, _box in deed_boxes(get_deed_record()):
        if _box["scan"] == page.name:
            _draw(_box["bbox"], TYPE_COLOURS[_label[0]], _label)
    for _scan, _bbox in get_pending_boxes():
        if _scan == page.name:
            _draw(_bbox, "grey", style="--")

    page_sel = mo.ui.matplotlib(_ax, debounce=True)
    # mo.ui.matplotlib shows the PNG at its pixel size (capped at 100% width): this box
    # keeps the on-screen size at FIG_H * 100 px whatever the quality.
    page_view = mo.Html(
        f'<div style="width: {round(100 * FIG_H * _w / _h)}px">{page_sel}</div>'
    )
    return page_sel, page_view


@app.cell(hide_code=True)
def _(get_pending_boxes, page, page_sel):
    MIN_BOX_PX = 3  # a plain click still yields a zero-area BoxSelection

    _v = page_sel.value
    drawn_box = None
    if (
        _v
        and hasattr(_v, "x_min")
        and _v.x_max - _v.x_min >= MIN_BOX_PX
        and _v.y_max - _v.y_min >= MIN_BOX_PX
    ):
        drawn_box = [
            round(_v.x_min),
            round(_v.y_min),
            round(_v.x_max),
            round(_v.y_max),
        ]

    # The unsaved block, in draw order: pending boxes, then the one drawn now.
    layout_boxes = get_pending_boxes() + (
        [(page.name, drawn_box)] if drawn_box else []
    )
    return drawn_box, layout_boxes


@app.cell(hide_code=True)
def zooms(book, crop, layout_boxes, mo):
    ZOOM_MAX = (
        3  # upscale cap: past 3x the scan's pixels a crop only gets blurrier
    )
    # The unsaved block at full resolution, in draw order, to read while transcribing.
    zooms = mo.vstack(
        [
            mo.image(
                crop(book / _scan, _bbox),
                style={
                    "width": "100%",
                    "max-width": f"{ZOOM_MAX * (_bbox[2] - _bbox[0])}px",
                },
            )
            for _scan, _bbox in layout_boxes
        ]
    )
    return (zooms,)


@app.cell(hide_code=True)
def block_buttons(
    add_block,
    annotator_name,
    block_labels,
    book,
    category_in,
    close_deed_record,
    delete_block,
    desc_in,
    drawn_box,
    get_deed_record,
    get_editing,
    get_editing_balance,
    get_editing_header,
    get_pending_boxes,
    layout_boxes,
    mo,
    page,
    pages,
    replace_block,
    save_deed_record,
    set_deed_record,
    set_editing,
    set_pending_boxes,
    set_type,
    split_label,
    type_radio,
    value_in,
):
    _names = [p.name for p in pages]
    # Editing the header or balance locks the items, as if closed.
    _locked = get_editing_header() or get_editing_balance()

    def _before_header(scan):
        # Nothing is continued, saved or closed there: it would be outside scans.
        return _names.index(scan) < _names.index(get_deed_record()["scans"][0])

    # Text shows amount and description start, so the list doubles as a typo check.
    _labels = {
        f"{label} · {item['amount']} · {item['description'][:30]}": label
        for label, item in block_labels(get_deed_record())
    }

    def _save(_):
        _fields = (
            type_radio.value,
            category_in.value,
            value_in.value,
            desc_in.value,
            layout_boxes,
        )
        if get_editing() is None:
            _deed_record = add_block(get_deed_record(), *_fields)
        else:
            _deed_record = replace_block(
                get_deed_record(), get_editing(), *_fields
            )
        _path = save_deed_record(book, _deed_record, annotator_name)
        set_deed_record(_deed_record)
        set_pending_boxes([])
        set_editing(None)
        mo.status.toast(f"saved {_path.name}")

    def _edit(_):
        if block_dd.value:
            _item = dict(block_labels(get_deed_record()))[block_dd.value]
            set_pending_boxes(
                [(_box["scan"], _box["bbox"]) for _box in _item["layout"]]
            )
            set_type(split_label(block_dd.value)[0])
            set_editing(block_dd.value)

    def _cancel_edit(_):
        set_editing(None)
        set_pending_boxes([])

    def _delete(_):
        if block_dd.value:
            _deed_record = delete_block(get_deed_record(), block_dd.value)
            _path = save_deed_record(book, _deed_record, annotator_name)
            set_deed_record(_deed_record)
            mo.status.toast(f"saved {_path.name}")

    def _close_person(_):
        _path = save_deed_record(
            book,
            close_deed_record(get_deed_record(), _names, page.name),
            annotator_name,
        )
        set_deed_record(None)  # no deed/person open until the next open
        set_type(None)
        mo.status.toast(f"saved {_path.name}, deed/person closed")

    continue_btn = mo.ui.button(
        label="continue",
        disabled=drawn_box is None
        or _locked
        or (get_deed_record() is not None and _before_header(page.name)),
        on_click=lambda _: set_pending_boxes(
            lambda p: p + [(page.name, drawn_box)]
        ),
    )
    # Discards a stray continue: needs no deed/person or type, unlike save.
    clear_pending_btn = mo.ui.button(
        label="clear pending",
        disabled=not get_pending_boxes(),
        on_click=lambda _: set_pending_boxes([]),
    )
    save_btn = mo.ui.button(
        label="save",
        disabled=get_deed_record() is None
        or _locked
        or not layout_boxes
        or type_radio.value is None
        or not (value_in.value.strip() or desc_in.value.strip())
        or any(_before_header(_scan) for _scan, _ in layout_boxes),
        on_click=_save,
    )
    block_dd = mo.ui.dropdown(options=_labels)
    # Edit loads the block into the inputs and its boxes into pending; save replaces it.
    edit_btn = mo.ui.button(
        label="edit",
        disabled=not _labels
        or bool(get_pending_boxes())
        or get_editing() is not None
        or _locked,
        on_click=_edit,
    )
    cancel_edit_btn = mo.ui.button(
        label="cancel edit",
        disabled=get_editing() is None,
        on_click=_cancel_edit,
    )
    delete_btn = mo.ui.button(
        label="delete",
        disabled=not _labels
        or get_editing() is not None  # labels would shift
        or _locked,
        on_click=_delete,
    )
    close_person_btn = mo.ui.button(
        label="close deed/person",
        disabled=get_deed_record() is None
        or bool(get_pending_boxes())
        or get_editing() is not None
        or _locked
        or _before_header(page.name),
        on_click=_close_person,
    )
    return (
        block_dd,
        cancel_edit_btn,
        clear_pending_btn,
        close_person_btn,
        continue_btn,
        delete_btn,
        edit_btn,
        save_btn,
    )


@app.cell(hide_code=True)
def book_dropdown(
    books,
    get_book_page,
    get_deed_record,
    get_pending_boxes,
    mo,
    root,
    set_book_page,
):
    # Picking a book moves to its first page. A person never crosses books, a pending block
    # belongs to this page. From the book index, not `book`: it stays when the book cell
    # stops. The path from the root tells apart same-named folders.
    _book_i = get_book_page()[0]
    book_dd = mo.ui.dropdown(
        options={str(b.relative_to(root)): i for i, b in enumerate(books)},
        value=str(books[_book_i].relative_to(root))
        if _book_i < len(books)
        else None,
        disabled=get_deed_record() is not None or bool(get_pending_boxes()),
        on_change=lambda i: set_book_page((i, 0)),
    )
    return (book_dd,)


@app.cell(hide_code=True)
def deed_picker(book, deed_choices, deeds, get_deed_record, mo):
    # The deed to open, or to go to, reopen or delete if it has a file; shown only while no
    # deed/person is open (`deed_row`). Re-created (cleared) on every open, write and close:
    # after a close nothing is picked, and the deeds with a file are up to date.
    get_deed_record()
    deed_dd = mo.ui.dropdown(
        options=deed_choices(deeds, book), searchable=True, label="deed"
    )
    # deed_id of the deed/person whose delete awaits confirmation; re-created (reset) with the
    # dropdown. Self loops: the button cell both reads and sets it.
    get_confirming_delete, set_confirming_delete = mo.state(
        None, allow_self_loops=True
    )
    return deed_dd, get_confirming_delete, set_confirming_delete


@app.cell(hide_code=True)
def deed_info(
    book,
    deed_choices,
    deed_dd,
    deeds,
    get_deed_record,
    mo,
    single_overledene,
):
    # The picked deed's overledene as in deeds.json, read only; while a deed/person is open,
    # its deed, as text: the dropdown pick is stale after a reopen.
    # Checked on pick, so only a deed that breaks the rule fails, not the whole book.
    _open = get_deed_record()
    _deed_id = deed_dd.value if _open is None else _open["deed_id"]
    _deed = deeds.get(_deed_id)
    deed_row = (
        deed_dd
        if _open is None
        else mo.md(
            "deed: "
            + {v: k for k, v in deed_choices(deeds, book).items()}.get(
                _deed_id, _deed_id
            )
        )
    )
    deed_details = mo.md("")
    openable_deed = None  # the picked deed, if open may write a file for it
    if _deed:
        try:
            _p = single_overledene(_deed)
            deed_details = mo.md(
                f"**{_p['naam_volledig']}** · died {_p['datum_overlijden']} in {_p['plaats_overlijden']}"
            )
            openable_deed = _deed if _open is None else None
        except ValueError as _e:
            deed_details = mo.callout(mo.md(str(_e)), kind="danger")
    return deed_details, deed_row, openable_deed


@app.cell(hide_code=True)
def deed_open(
    annotator_name,
    book,
    deed_path,
    drawn_box,
    get_deed_record,
    get_editing_header,
    mo,
    new_deed_record,
    openable_deed,
    page,
    save_deed_record,
    set_deed_id,
    set_deed_record,
):
    # Its own cell, after the deed row: the click sets the deed/person, and a cell does not
    # rerun on state it sets itself. This one reruns through `openable_deed`.
    def _open(_):
        # Checked again here: another tab (its own session) may have opened it meanwhile.
        if deed_path(book, openable_deed["deed_id"]).exists():
            mo.status.toast("this deed already has a file: reopen it instead")
            return
        # The box drawn now is the header: kept in the file, the redraw drops it.
        _deed_record = new_deed_record(openable_deed, page.name, drawn_box)
        _path = save_deed_record(
            book, _deed_record, annotator_name
        )  # at once: one file per deed
        set_deed_id(_deed_record["deed_id"])
        set_deed_record(_deed_record)
        mo.status.toast(f"saved {_path.name}, deed/person open")

    open_btn = mo.ui.button(
        label="open",
        # A deed with a file is reopened, not opened anew. No header box, no open.
        disabled=openable_deed is None
        or drawn_box is None
        or deed_path(book, openable_deed["deed_id"]).exists(),
        on_click=_open,
    )
    # The header box is easy to miss: say so until one is drawn, also when redrawn.
    _hint = (
        "Draw the new header box and click **save header**"
        if get_editing_header()
        else "Draw a box around the header and click **open**"
        if get_deed_record() is None
        else ""
    )
    open_hint = mo.md(_hint if drawn_box is None else "")
    return open_btn, open_hint


@app.cell(hide_code=True)
def header_buttons(
    annotator_name,
    book,
    drawn_box,
    get_deed_record,
    get_editing,
    get_editing_balance,
    get_editing_header,
    get_pending_boxes,
    mo,
    page,
    pages,
    save_deed_record,
    set_deed_record,
    set_editing_header,
    set_header,
):
    # Edit header locks the balance and items, as if closed. Save header saves the drawn box
    # as the header, like open, on any page with no saved box before it: that is the new
    # header page.
    _names = [p.name for p in pages]
    _deed_record = None
    if get_editing_header() and drawn_box is not None:
        try:
            _deed_record = set_header(
                get_deed_record(), _names, page.name, drawn_box
            )
        except ValueError:
            pass  # a saved box before this page: save header stays disabled

    def _save_header(_):
        _path = save_deed_record(book, _deed_record, annotator_name)
        set_deed_record(_deed_record)
        set_editing_header(False)
        mo.status.toast(f"saved {_path.name}")

    edit_header_btn = mo.ui.button(
        label="edit header",
        disabled=get_deed_record() is None
        or bool(get_pending_boxes())
        or get_editing() is not None
        or get_editing_header()
        or get_editing_balance(),
        on_click=lambda _: set_editing_header(True),
    )
    save_header_btn = mo.ui.button(
        label="save header",
        disabled=_deed_record is None,
        on_click=_save_header,
    )
    # Keeps the old box.
    cancel_header_btn = mo.ui.button(
        label="cancel header edit",
        disabled=not get_editing_header(),
        on_click=lambda _: set_editing_header(False),
    )
    return cancel_header_btn, edit_header_btn, save_header_btn


@app.cell(hide_code=True)
def deed_file_buttons(
    book,
    deed_dd,
    deed_path,
    get_confirming_delete,
    get_deed_record,
    get_pending_boxes,
    load_deed_records,
    mo,
    pages,
    set_book_page,
    set_confirming_delete,
    set_deed_id,
    set_deed_record,
    set_type,
):
    # Like the jump's go: a person never crosses books, a pending block belongs to this page.
    # Only for a deed with a file; one without is opened instead.
    _disabled = (
        deed_dd.value is None
        or not deed_path(book, deed_dd.value).exists()
        or get_deed_record() is not None
        or bool(get_pending_boxes())
    )

    def _read_picked_file():
        # Read at click: another tab (its own session) may have rewritten the file.
        _deed_record = load_deed_records(book)[deed_dd.value]
        return _deed_record, [p.name for p in pages].index(
            _deed_record["scans"][0]
        )

    go_to_btn = mo.ui.button(
        label="go to deed/person",
        disabled=_disabled,
        on_click=lambda _: set_book_page(
            lambda book_page: (book_page[0], _read_picked_file()[1])
        ),
    )

    def _reopen(_):
        # The picked deed/person is open again, as if never closed: save, delete and
        # close then rewrite its file.
        _deed_record, _header_page_i = _read_picked_file()
        set_deed_id(deed_dd.value)
        set_deed_record(_deed_record)
        set_type(None)
        set_book_page(lambda book_page: (book_page[0], _header_page_i))

    # Disabled like go; an edit needs an open person, so that is covered too.
    reopen_btn = mo.ui.button(
        label="reopen", disabled=_disabled, on_click=_reopen
    )

    def _delete_file(_):
        _path = deed_path(book, deed_dd.value)
        _path.unlink()
        mo.status.toast(f"deleted {_path.name}")
        # Still None: this rebuilds the dropdown, the faded boxes and the debug pane.
        set_deed_record(None)

    # Two steps: delete deed/person, then confirm or cancel. Picking another deed shows
    # delete deed/person again.
    if not _disabled and get_confirming_delete() == deed_dd.value:
        delete_file_ui = mo.hstack(
            [
                mo.ui.button(
                    label=f"confirm delete {deed_path(book, deed_dd.value).stem}",
                    on_click=_delete_file,
                ),
                mo.ui.button(
                    label="cancel",
                    on_click=lambda _: set_confirming_delete(None),
                ),
            ],
            justify="start",
        )
    else:
        delete_file_ui = mo.ui.button(
            label="delete deed/person",
            disabled=_disabled,
            on_click=lambda _: set_confirming_delete(deed_dd.value),
        )
    return delete_file_ui, go_to_btn, reopen_btn


@app.cell(hide_code=True)
def deed_move_picker(
    book,
    deed_choices,
    deed_path,
    deeds,
    get_deed_record,
    mo,
):
    # The deed to move the open deed/person's labels to: one without a file. Re-created
    # (cleared) on every open, write and close, so the deeds with a file are up to date.
    get_deed_record()
    move_dd = mo.ui.dropdown(
        options={
            _label: _deed_id
            for _label, _deed_id in deed_choices(deeds, book).items()
            if not deed_path(book, _deed_id).exists()
        },
        searchable=True,
        label="move to",
    )
    return (move_dd,)


@app.cell(hide_code=True)
def deed_move(
    annotator_name,
    book,
    deed_path,
    deeds,
    get_deed_record,
    get_editing,
    get_editing_balance,
    get_editing_header,
    get_pending_boxes,
    mo,
    move_dd,
    move_deed_record,
    set_deed_id,
    set_deed_record,
):
    # Moves the open deed/person's labels to the picked deed: same rules as close deed/person.
    # It stays open, under the new deed; its old deed has no file again.
    def _move(_):
        try:
            _deed_record = move_deed_record(
                book, get_deed_record(), deeds[move_dd.value], annotator_name
            )
        # The deed cannot be used, or another tab opened it meanwhile.
        except ValueError as _e:
            mo.status.toast(str(_e))
            return
        set_deed_id(_deed_record["deed_id"])
        set_deed_record(_deed_record)
        mo.status.toast(
            f"saved {deed_path(book, _deed_record['deed_id']).name}, labels moved"
        )

    move_btn = mo.ui.button(
        label="move labels",
        disabled=move_dd.value is None
        or bool(get_pending_boxes())
        or get_editing() is not None
        or get_editing_header()
        or get_editing_balance(),
        on_click=_move,
    )
    # Only while a deed/person is open: there are no labels to move otherwise.
    move_ui = (
        mo.hstack([move_dd, move_btn], justify="start", align="end")
        if get_deed_record() is not None
        else mo.md("")
    )
    return (move_ui,)


@app.cell(hide_code=True)
def balance_inputs(get_deed_record, get_editing_balance, mo):
    # The balance's totals: its saved values, read only, while it has one (a typo check),
    # unless it is edited. Re-created on every open, write, close and balance edit or cancel;
    # clear balance box empties them again.
    _open = get_deed_record()
    _balance = (_open and _open["annotation"]["balance"]) or {}
    # debounce: save box as balance enables while typing, as for the item value
    total_assets_in, total_liabilities_in, total_in = (
        mo.ui.text(
            label=_field.replace("_", " "),
            value=_balance.get(_field, ""),
            disabled=bool(_balance) and not get_editing_balance(),
            debounce=300,
        )
        for _field in ["total_assets", "total_liabilities", "total"]
    )
    return total_assets_in, total_in, total_liabilities_in


@app.cell(hide_code=True)
def balance_buttons(
    annotator_name,
    book,
    clear_balance,
    drawn_box,
    get_deed_record,
    get_editing,
    get_editing_balance,
    get_editing_header,
    get_pending_boxes,
    mo,
    page,
    pages,
    replace_balance,
    save_deed_record,
    set_balance,
    set_deed_record,
    set_editing_balance,
    total_assets_in,
    total_in,
    total_liabilities_in,
):
    _open = get_deed_record()
    _balance = _open and _open["annotation"]["balance"]
    _editing = get_editing_balance()
    # The drawn box; while editing, with none drawn, the saved one is kept.
    _box = (
        (page.name, drawn_box)
        if drawn_box is not None
        else (_balance["layout"]["scan"], _balance["layout"]["bbox"])
        if _editing
        else None
    )

    def _save_balance(_):
        _deed_record = (replace_balance if _editing else set_balance)(
            get_deed_record(),
            *_box,
            total_assets_in.value,
            total_liabilities_in.value,
            total_in.value,
        )
        _path = save_deed_record(book, _deed_record, annotator_name)
        set_deed_record(_deed_record)
        set_editing_balance(False)
        mo.status.toast(f"saved {_path.name}")

    def _clear_balance(_):
        _deed_record = clear_balance(get_deed_record())
        _path = save_deed_record(book, _deed_record, annotator_name)
        set_deed_record(_deed_record)
        mo.status.toast(f"saved {_path.name}")

    _names = [p.name for p in pages]
    save_balance_btn = mo.ui.button(
        label="save box as balance",
        # At most one: clear or edit balance box first. Not before the header page:
        # outside scans.
        disabled=_open is None
        or get_editing_header()
        or (bool(_balance) and not _editing)
        or _box is None
        or _names.index(_box[0]) < _names.index(_open["scans"][0])
        or not any(
            _in.value.strip()
            for _in in [total_assets_in, total_liabilities_in, total_in]
        ),
        on_click=_save_balance,
    )
    # Removes the balance, box and totals: then a new box can be saved as balance.
    clear_balance_btn = mo.ui.button(
        label="clear balance box",
        disabled=not _balance or get_editing_header() or _editing,
        on_click=_clear_balance,
    )
    # Unlocks the totals; save box as balance then rewrites the balance. Locks the header
    # and items, as edit header does.
    edit_balance_btn = mo.ui.button(
        label="edit balance box",
        disabled=not _balance
        or bool(get_pending_boxes())
        or get_editing() is not None
        or get_editing_header()
        or _editing,
        on_click=lambda _: set_editing_balance(True),
    )
    # Keeps the saved balance.
    cancel_balance_btn = mo.ui.button(
        label="cancel balance edit",
        disabled=not _editing,
        on_click=lambda _: set_editing_balance(False),
    )
    return (
        cancel_balance_btn,
        clear_balance_btn,
        edit_balance_btn,
        save_balance_btn,
    )


@app.cell(hide_code=True)
def debug_toggle(mo):
    # `-- --debug` only: hides the debug elements (not itself), e.g. for a demo.
    debug_switch = (
        mo.ui.switch(label="debug", value=True)
        if "debug" in mo.cli_args()
        else None
    )
    return (debug_switch,)


@app.cell(hide_code=True)
def status_line(
    book,
    deed_path,
    get_deed_record,
    get_editing,
    get_editing_balance,
    get_editing_header,
    get_pending_boxes,
    mo,
    page,
    page_i,
    pages,
):
    # Its own cell, not in `layout`: a click reruns `layout` at once (it shows the buttons), with
    # the new state but the old elements. This cell reruns only with the rebuilt elements, so
    # the status line never says "no deed/person" while the old person dropdown is still showing.
    _open = get_deed_record()
    _deed = (
        f"editing {deed_path(book, _open['deed_id']).stem}"
        if _open
        else "no deed/person"
    )
    status_line = mo.md(
        f"`{book.name}/{page.name}` · {_deed} · page {page_i + 1}/{len(pages)} · pending {len(get_pending_boxes())}"
        + (f" · editing {get_editing()}" if get_editing() else "")
        + (" · editing header" if get_editing_header() else "")
        + (" · editing balance" if get_editing_balance() else "")
    )
    return (status_line,)


@app.cell(hide_code=True)
def layout(
    annotator_row,
    block_dd,
    book,
    book_dd,
    cancel_balance_btn,
    cancel_edit_btn,
    cancel_header_btn,
    category_in,
    clear_balance_btn,
    clear_pending_btn,
    close_person_btn,
    continue_btn,
    debug_switch,
    deed_details,
    deed_path,
    deed_row,
    delete_btn,
    delete_file_ui,
    desc_in,
    edit_balance_btn,
    edit_btn,
    edit_header_btn,
    fig_h_slider,
    get_deed_id,
    go_to_btn,
    mo,
    move_ui,
    next_page_btn,
    open_btn,
    open_hint,
    page_view,
    prev_page_btn,
    quality_slider,
    reopen_btn,
    save_balance_btn,
    save_btn,
    save_header_btn,
    status_line,
    total_assets_in,
    total_in,
    total_liabilities_in,
    type_radio,
    value_in,
    zooms,
):
    _page_column = mo.vstack(
        [page_view, mo.hstack([quality_slider, fig_h_slider], justify="start")]
    )
    # Top to bottom, from the widest scope to the narrowest, split by rules: annotator, book
    # and deed/person, balance, page, block.
    _form = mo.vstack(
        [
            annotator_row,
            mo.hstack(
                [debug_switch, status_line], justify="start", align="center"
            )
            if debug_switch is not None
            else status_line,
            book_dd,
            mo.hstack(
                [deed_row, deed_details, move_ui],
                justify="start",
                align="center",
            ),
            open_hint,
            mo.hstack(
                [
                    open_btn,
                    go_to_btn,
                    reopen_btn,
                    delete_file_ui,
                    edit_header_btn,
                    save_header_btn,
                    cancel_header_btn,
                    close_person_btn,
                ],
                justify="start",
            ),
            mo.md("---"),
            mo.hstack(
                [total_assets_in, total_liabilities_in, total_in],
                justify="start",
            ),
            mo.hstack(
                [
                    save_balance_btn,
                    edit_balance_btn,
                    cancel_balance_btn,
                    clear_balance_btn,
                ],
                justify="start",
            ),
            mo.md("---"),
            mo.hstack([prev_page_btn, next_page_btn], justify="start"),
            mo.md("---"),
            mo.hstack([type_radio, category_in, value_in], justify="start"),
            desc_in,
            mo.hstack(
                [continue_btn, clear_pending_btn, save_btn], justify="start"
            ),
            mo.hstack(
                [block_dd, edit_btn, cancel_edit_btn, delete_btn],
                justify="start",
            ),
        ]
    )
    # `-- --debug`, switch on: the open (or last closed) deed/person's file right of the form.
    # Built here, not in its own cell: an extra cell re-renders the layout twice per write.
    if debug_switch is not None and debug_switch.value:
        _path = deed_path(book, get_deed_id()) if get_deed_id() else None
        _form = mo.hstack(
            [
                _form,
                mo.vstack(
                    [
                        mo.md(
                            "**DEBUG PANE**"
                            + (f" · `{_path.name}`" if _path else "")
                        ),
                        mo.md(f"```json\n{_path.read_text()}\n```")
                        if _path and _path.exists()
                        else mo.md("no file yet"),
                    ]
                ).style(
                    max_height="20rem",
                    overflow="auto",
                    border="3px solid lime",
                    padding="0.5rem",
                ),
            ],
            widths=[1, 1],
            align="start",
        )
    # Page at its fixed size on the left; form and zooms take the rest of the width.
    # None = no flex: a 0 would let the page column shrink to nothing.
    mo.hstack(
        [_page_column, mo.vstack([_form, zooms])],
        widths=[None, 1],
        align="start",
    )
    return


@app.cell(hide_code=True)
def jump_slider(annotator_name, book_pages, get_book_page, mo):
    mo.stop(not annotator_name)  # the locked name comes first, as for the form
    # Every page of every book in labeling order: the slider position is overall progress.
    all_pages = [
        (b, p)
        for b, _pages in enumerate(book_pages)
        for p in range(len(_pages))
    ]
    _here = get_book_page()  # (len(books), 0) once all books are done
    jump_slider = mo.ui.slider(
        1,
        len(all_pages),
        value=all_pages.index(_here) + 1
        if _here in all_pages
        else len(all_pages),
        label="all pages",
        show_value=True,
        include_input=True,
        full_width=True,
        debounce=True,
    )
    return all_pages, jump_slider


@app.cell(hide_code=True)
def jump_strip(
    all_pages,
    book_pages,
    books,
    get_book_page,
    get_deed_record,
    get_pending_boxes,
    jump_slider,
    mo,
    set_book_page,
    thumbnail,
):
    THUMB_SPAN = 4  # pages shown on each side of the slider position
    _i = jump_slider.value - 1
    _target = all_pages[_i]
    _here = get_book_page()
    # A person never crosses books, and a pending block belongs to this page: while either
    # is open the slider and strip are view only.
    jump_btn = mo.ui.button(
        label="go",
        disabled=get_deed_record() is not None
        or bool(get_pending_boxes())
        or _target == _here,
        on_click=lambda _: set_book_page(_target),
    )

    # One segment per folder, sized by its page count (hover: name); solid = current page,
    # dashed = slider position, both in the text colour so they show on any segment.
    # Not pixel-aligned with the slider track (wishlist).
    _n = len(all_pages)
    # Okabe-Ito (colour-blind safe), without black, which vanishes in dark mode.
    OKABE_ITO = [
        "#E69F00",
        "#56B4E9",
        "#009E73",
        "#F0E442",
        "#0072B2",
        "#D55E00",
        "#CC79A7",
    ]
    _segments = "".join(
        f'<div title="{_book.name}: {len(_pages)} pages" style="flex: {len(_pages)}; '
        f"background: {OKABE_ITO[_k % len(OKABE_ITO)]}99; overflow: hidden; "
        f'white-space: nowrap; text-overflow: ellipsis; font-size: 11px; padding: 0 4px">'
        f"{_book.name}</div>"
        for _k, (_book, _pages) in enumerate(zip(books, book_pages))
    )

    def _marker(j, css):
        return f'<div style="position: absolute; top: 0; bottom: 0; left: {100 * (j + 0.5) / _n}%; {css}"></div>'

    folder_bar = mo.Html(
        '<div style="position: relative; display: flex; height: 18px">'
        + _segments
        + _marker(
            all_pages.index(_here) if _here in all_pages else _n - 1,
            "border-left: 3px solid currentColor",
        )
        + _marker(_i, "border-left: 2px dashed currentColor")
        + "</div>"
    )

    def _thumb(j):
        _b, _p = all_pages[j]
        _style = (
            {"outline": "3px solid currentColor"} if (_b, _p) == _here else {}
        )
        if j == _i:
            _style = {**_style, "border": "3px dashed currentColor"}
        return mo.image(
            thumbnail(book_pages[_b][_p], 100),
            height=100,
            style=_style,
            caption=f"{j + 1}" + (f" {books[_b].name}" if _p == 0 else ""),
        )

    mo.vstack(
        [
            mo.hstack(
                [
                    jump_slider,
                    # Plain text, not code: the status line already has `<folder>/<file>`.
                    mo.md(
                        f"/ {len(all_pages)} · {books[_target[0]].name}/{book_pages[_target[0]][_target[1]].name}"
                    ),
                    jump_btn,
                ],
                align="center",
                widths=[6, 3, 1],
            ),
            folder_bar,
            mo.hstack(
                [
                    _thumb(j)
                    for j in range(
                        max(0, _i - THUMB_SPAN),
                        min(len(all_pages), _i + THUMB_SPAN + 1),
                    )
                ],
                justify="start",
            ),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
