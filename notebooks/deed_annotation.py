import marimo

__generated_with = "0.25.1"
app = marimo.App(width="full")


@app.cell
def imports():
    from pathlib import Path

    import marimo as mo

    from vox_paginae import marimo_ui
    from vox_paginae.annotation import (
        add_balance_box,
        add_header_box,
        add_item,
        close_deed_record,
        deed_boxes,
        deed_path,
        delete_balance_box,
        delete_header_box,
        delete_item,
        item_tags,
        list_pages,
        load_deed_records,
        move_deed_record,
        new_deed_record,
        next_page,
        replace_item,
        resume,
        save_deed_record,
        saved_boxes,
        set_balance_totals,
        set_header_fields,
        split_tag,
    )
    from vox_paginae.book_input import (
        copied_deed_person_data,
        deed_choices,
        find_books,
        header_fields,
        load_deeds,
        single_overledene,
    )
    from vox_paginae.ui import (
        draw_scan,
        item_option,
        scan_for_display,
        selection_box,
        status_text,
    )

    return (
        Path,
        add_balance_box,
        add_header_box,
        add_item,
        close_deed_record,
        copied_deed_person_data,
        deed_boxes,
        deed_choices,
        deed_path,
        delete_balance_box,
        delete_header_box,
        delete_item,
        draw_scan,
        find_books,
        header_fields,
        item_option,
        item_tags,
        list_pages,
        load_deed_records,
        load_deeds,
        marimo_ui,
        mo,
        move_deed_record,
        new_deed_record,
        next_page,
        replace_item,
        resume,
        save_deed_record,
        saved_boxes,
        scan_for_display,
        selection_box,
        set_balance_totals,
        set_header_fields,
        single_overledene,
        split_tag,
        status_text,
    )


@app.cell
def _(Path, marimo_ui, mo):
    # `marimo edit|run notebooks/deed_annotation.py -- --data-root <dir>` overrides the default.
    default_root = Path(mo.cli_args().get("data-root") or Path.home())
    root_picker = marimo_ui.root_picker(default_root)
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
def annotator_input(get_annotator, marimo_ui):
    _name, _locked = get_annotator()
    annotator_in = marimo_ui.annotator_input(_name, _locked)
    # A plain name for now: every write records it. "" until locked: nothing past the
    # book cell runs. From the state, not the input, so typing reruns nothing below.
    annotator_name = _name if _locked else ""
    return annotator_in, annotator_name


@app.cell(hide_code=True)
def annotator_lock(annotator_in, get_annotator, marimo_ui, set_annotator):
    annotator_row = marimo_ui.annotator_row(
        annotator_in, get_annotator, set_annotator
    )
    return (annotator_row,)


@app.cell(hide_code=True)
def session_state(find_books, list_pages, mo, resume, root):
    books = find_books(root)
    book_pages = [list_pages(b) for b in books]
    # Everything below resets when the root changes.
    get_book_page, set_book_page = mo.state(
        resume(books)
    )  # (book index, page index)
    # None = no deed open: one is opened from the deed row. Resume never reopens
    # one, so this always starts as None.
    get_deed_record, set_deed_record = mo.state(None)
    # deed_id of the open (or last closed) deed: the debug pane shows its file.
    get_deed_id, set_deed_id = mo.state(None)
    get_pending_boxes, set_pending_boxes = mo.state(
        []
    )  # (scan, bbox) pending boxes of the item being drawn
    # Tag ("A2") of the item loaded by edit: save replaces it. None = save adds an item.
    get_editing, set_editing = mo.state(None)
    # Type to prefill the radio with. Set only on edit and close, so a save keeps the last
    # type used without rebuilding the radio.
    get_type, set_type = mo.state(None)
    return (
        book_pages,
        books,
        get_book_page,
        get_deed_id,
        get_deed_record,
        get_editing,
        get_pending_boxes,
        get_type,
        set_book_page,
        set_deed_id,
        set_deed_record,
        set_editing,
        set_pending_boxes,
        set_type,
    )


@app.cell(hide_code=True)
def page_buttons(
    book_pages,
    close_deed_record,
    get_deed_record,
    get_editing,
    get_pending_boxes,
    mo,
    next_page,
    page,
    page_i,
    pages,
    save_open_deed,
    set_book_page,
    set_deed_record,
    set_type,
):
    _last_page = page_i == len(pages) - 1

    def _next_page(_):
        if (
            _last_page
        ):  # a deed never crosses books: close the open one, if any
            if get_deed_record() is not None:
                try:
                    _deed_record = close_deed_record(
                        get_deed_record(), [p.name for p in pages], page.name
                    )
                except (
                    ValueError
                ) as _e:  # no header box or a blank field: it stays open, here
                    mo.status.toast(str(_e))
                    return
                _path = save_open_deed(_deed_record)
                mo.status.toast(f"saved {_path.name}, deed closed")
            set_deed_record(None)
            set_type(None)
        set_book_page(
            lambda book_page: next_page(
                book_page, [len(p) for p in book_pages]
            )
        )

    next_page_btn = mo.ui.button(
        label="next page",
        # On the last page it closes the open deed: same rules as close deed.
        disabled=_last_page
        and (bool(get_pending_boxes()) or get_editing() is not None),
        on_click=_next_page,
    )
    # Stays inside the current book: a deed never crosses books.
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
def _(get_deed_record, get_editing, item_tags, mo):
    get_deed_record()  # re-created (cleared) after every open, write and close
    # Prefilled from the item being edited, if any.
    _item = dict(item_tags(get_deed_record())).get(get_editing(), {})
    category_in = mo.ui.text(
        label="category", value=_item.get("category") or ""
    )
    # debounce=False: save enables while typing. Not debounce=300: marimo's timed
    # debounce can send back a value the kernel replaced, e.g. edit then cancel edit (#11).
    amount_in = mo.ui.text(
        label="amount", value=_item.get("amount", ""), debounce=False
    )
    desc_in = mo.ui.text(
        label="description",
        value=_item.get("description", ""),
        full_width=True,
        debounce=False,
    )
    return amount_in, category_in, desc_in


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
def deed_save(annotator_name, book, deed_path, save_deed_record):
    # Every write goes to the open deed's own file, by the locked annotator.
    def save_open_deed(deed_record):
        return save_deed_record(
            deed_path(book, deed_record["deed_id"]),
            deed_record,
            annotator_name,
        )

    return (save_open_deed,)


@app.cell(hide_code=True)
def view_sliders(marimo_ui):
    quality_slider, fig_h_slider = marimo_ui.view_sliders()
    return fig_h_slider, quality_slider


@app.cell(hide_code=True)
def _(fig_h_slider, page, quality_slider, scan_for_display):
    scan_pixels, scan_size, png_dpi = scan_for_display(
        page, fig_h_slider.value, quality_slider.value
    )
    return png_dpi, scan_pixels, scan_size


@app.cell(hide_code=True, expand_output=True)
def _(
    book,
    deed_boxes,
    draw_scan,
    fig_h_slider,
    get_deed_id,
    get_deed_record,
    get_pending_boxes,
    marimo_ui,
    page,
    png_dpi,
    saved_boxes,
    scan_pixels,
    scan_size,
):
    FIG_H = fig_h_slider.value  # inches, shown at 100 px each

    # Saved boxes of other deeds (and of a closed one), faded: shared pages, restarts.
    _editing = get_deed_id() if get_deed_record() is not None else None
    _ax = draw_scan(
        scan_pixels,
        scan_size,
        FIG_H,
        png_dpi,
        saved=saved_boxes(book, page.name, _editing),
        deed=[
            (_tag, _box["bbox"])
            for _tag, _box in deed_boxes(get_deed_record())
            if _box["scan"] == page.name
        ],
        pending=[
            _bbox for _scan, _bbox in get_pending_boxes() if _scan == page.name
        ],
    )

    page_sel, page_view = marimo_ui.page_view(_ax, scan_size, FIG_H)
    return page_sel, page_view


@app.cell(hide_code=True)
def _(get_pending_boxes, page, page_sel, selection_box):
    drawn_box = selection_box(page_sel.value)

    # The unsaved item, in draw order: pending boxes, then the one drawn now.
    layout_boxes = get_pending_boxes() + (
        [(page.name, drawn_box)] if drawn_box else []
    )
    return drawn_box, layout_boxes


@app.cell(hide_code=True)
def zooms(book, layout_boxes, marimo_ui):
    # The unsaved item at full resolution, in draw order, to read while transcribing.
    zooms = marimo_ui.zooms(book, layout_boxes)
    return (zooms,)


@app.cell(hide_code=True)
def item_buttons(
    add_item,
    amount_in,
    category_in,
    close_deed_record,
    delete_item,
    desc_in,
    drawn_box,
    get_deed_record,
    get_editing,
    get_pending_boxes,
    item_option,
    item_tags,
    layout_boxes,
    mo,
    page,
    pages,
    replace_item,
    save_open_deed,
    set_deed_record,
    set_editing,
    set_pending_boxes,
    set_type,
    split_tag,
    type_radio,
):
    _names = [p.name for p in pages]

    def _before_first_scan(scan):
        # Nothing is continued, saved or closed there: it would be outside scans.
        return _names.index(scan) < _names.index(get_deed_record()["scans"][0])

    _tags = {
        item_option(tag, item): tag
        for tag, item in item_tags(get_deed_record())
    }

    def _save(_):
        _fields = (
            type_radio.value,
            category_in.value,
            amount_in.value,
            desc_in.value,
            layout_boxes,
        )
        if get_editing() is None:
            _deed_record = add_item(get_deed_record(), *_fields)
        else:
            _deed_record = replace_item(
                get_deed_record(), get_editing(), *_fields
            )
        _path = save_open_deed(_deed_record)
        set_deed_record(_deed_record)
        set_pending_boxes([])
        set_editing(None)
        mo.status.toast(f"saved {_path.name}")

    def _edit(_):
        if item_dd.value:
            _item = dict(item_tags(get_deed_record()))[item_dd.value]
            set_pending_boxes(
                [(_box["scan"], _box["bbox"]) for _box in _item["layout"]]
            )
            set_type(split_tag(item_dd.value)[0])
            set_editing(item_dd.value)

    def _cancel_edit(_):
        set_editing(None)
        set_pending_boxes([])

    def _delete(_):
        if item_dd.value:
            _deed_record = delete_item(get_deed_record(), item_dd.value)
            _path = save_open_deed(_deed_record)
            set_deed_record(_deed_record)
            mo.status.toast(f"saved {_path.name}")

    def _close_deed(_):
        try:
            _deed_record = close_deed_record(
                get_deed_record(), _names, page.name
            )
        except (
            ValueError
        ) as _e:  # no header box or a blank field: it stays open
            mo.status.toast(str(_e))
            return
        _path = save_open_deed(_deed_record)
        set_deed_record(None)  # no deed open until the next open
        set_type(None)
        mo.status.toast(f"saved {_path.name}, deed closed")

    continue_btn = mo.ui.button(
        label="continue",
        disabled=drawn_box is None
        or (get_deed_record() is not None and _before_first_scan(page.name)),
        on_click=lambda _: set_pending_boxes(
            lambda p: p + [(page.name, drawn_box)]
        ),
    )
    # Discards a stray continue: needs no deed or type, unlike save.
    clear_pending_btn = mo.ui.button(
        label="clear pending",
        disabled=not get_pending_boxes(),
        on_click=lambda _: set_pending_boxes([]),
    )
    save_btn = mo.ui.button(
        label="save",
        disabled=get_deed_record() is None
        or not layout_boxes
        or type_radio.value is None
        or not (amount_in.value.strip() or desc_in.value.strip())
        or any(_before_first_scan(_scan) for _scan, _ in layout_boxes),
        on_click=_save,
    )
    item_dd = mo.ui.dropdown(options=_tags)
    # Edit loads the item into the inputs and its boxes into pending; save replaces it.
    edit_btn = mo.ui.button(
        label="edit",
        disabled=not _tags
        or bool(get_pending_boxes())
        or get_editing() is not None,
        on_click=_edit,
    )
    cancel_edit_btn = mo.ui.button(
        label="cancel edit",
        disabled=get_editing() is None,
        on_click=_cancel_edit,
    )
    delete_btn = mo.ui.button(
        label="delete",
        disabled=not _tags or get_editing() is not None,  # tags would shift
        on_click=_delete,
    )
    close_deed_btn = mo.ui.button(
        label="close deed",
        disabled=get_deed_record() is None
        or bool(get_pending_boxes())
        or get_editing() is not None
        or _before_first_scan(page.name),
        on_click=_close_deed,
    )
    return (
        cancel_edit_btn,
        clear_pending_btn,
        close_deed_btn,
        continue_btn,
        delete_btn,
        edit_btn,
        item_dd,
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
    # Picking a book moves to its first page. A deed never crosses books, pending boxes
    # belong to this page. From the book index, not `book`: it stays when the book cell
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
    # deed is open (`deed_row`). Re-created (cleared) on every open, write and close:
    # after a close nothing is picked, and the deeds with a file are up to date.
    get_deed_record()
    deed_dd = mo.ui.dropdown(
        options=deed_choices(deeds, book), searchable=True, label="deed"
    )
    # deed_id of the deed whose delete awaits confirmation; re-created (reset) with the
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
    # The picked deed's overledene as in deeds.json, read only; while a deed is open,
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
    book,
    copied_deed_person_data,
    deed_path,
    drawn_box,
    get_deed_record,
    header_fields,
    mo,
    new_deed_record,
    openable_deed,
    page,
    save_open_deed,
    set_deed_id,
    set_deed_record,
    set_header_fields,
):
    # Its own cell, after the deed row: the click sets the deed, and a cell does not
    # rerun on state it sets itself. This one reruns through `openable_deed`.
    def _open(_):
        # Checked again here: another tab (its own session) may have opened it meanwhile.
        if deed_path(book, openable_deed["deed_id"]).exists():
            mo.status.toast("this deed already has a file: reopen it instead")
            return
        # This scan is its first scan; its header boxes are saved after. Its header
        # fields start as the deed's copied data.
        _copied = copied_deed_person_data(openable_deed)
        _deed_record = set_header_fields(
            new_deed_record(openable_deed["deed_id"], _copied, page.name),
            **header_fields(_copied),
        )
        _path = save_open_deed(_deed_record)  # at once: one file per deed
        set_deed_id(_deed_record["deed_id"])
        set_deed_record(_deed_record)
        mo.status.toast(f"saved {_path.name}, deed open")

    open_btn = mo.ui.button(
        label="open",
        # A deed with a file is reopened, not opened anew.
        disabled=openable_deed is None
        or deed_path(book, openable_deed["deed_id"]).exists(),
        on_click=_open,
    )
    # The header box is easy to miss: say so until the open deed has one and while
    # none is drawn. Close would refuse it.
    _record = get_deed_record()
    open_hint = mo.md(
        "Draw a box around the header and click **save box as header**"
        if _record is not None
        and not _record["annotation"]["header"]["layout"]
        and drawn_box is None
        else ""
    )
    return open_btn, open_hint


@app.cell(hide_code=True)
def header_inputs(get_deed_record, mo):
    # The header's fields, editable while a deed is open and showing its saved values:
    # pre-filled on open from the deed's copied data. Re-created on every open, write and
    # close: fields typed but not saved are then gone.
    _open = get_deed_record()
    _header = _open["annotation"]["header"] if _open else {}
    # debounce=False: the value is in before a click on save header fields, as for the
    # balance totals
    full_name_in, date_of_death_in, place_of_residence_in = (
        mo.ui.text(
            label=_field.replace("_", " "),
            value=_header.get(_field, ""),
            disabled=_open is None,
            debounce=False,
        )
        for _field in ["full_name", "date_of_death", "place_of_residence"]
    )
    return date_of_death_in, full_name_in, place_of_residence_in


@app.cell(hide_code=True)
def header_buttons(
    add_header_box,
    date_of_death_in,
    deed_boxes,
    delete_header_box,
    drawn_box,
    full_name_in,
    get_deed_record,
    get_editing,
    get_pending_boxes,
    mo,
    page,
    pages,
    place_of_residence_in,
    save_open_deed,
    set_deed_record,
    set_header_fields,
):
    # Header boxes go in one at a time, like the balance's, on the deed's first scan or a
    # later one: before it they would be outside scans. Each has its own tag: H1, H2…
    _open = get_deed_record()
    _names = [p.name for p in pages]
    _tags = {
        f"{_tag} · page {_names.index(_box['scan']) + 1}": _tag
        for _tag, _box in deed_boxes(_open)
        if _tag[0] == "H"
    }
    # Editing an item locks the header, as if closed.
    _locked = get_editing() is not None

    def _save_header_box(_):
        _deed_record = add_header_box(get_deed_record(), page.name, drawn_box)
        _path = save_open_deed(_deed_record)
        set_deed_record(_deed_record)
        mo.status.toast(f"saved {_path.name}")

    def _save_header_fields(_):
        _deed_record = set_header_fields(
            get_deed_record(),
            full_name_in.value,
            date_of_death_in.value,
            place_of_residence_in.value,
        )
        _path = save_open_deed(_deed_record)
        set_deed_record(_deed_record)
        mo.status.toast(f"saved {_path.name}")

    def _delete_header_box(_):
        if header_dd.value:
            _deed_record = delete_header_box(
                get_deed_record(), header_dd.value
            )
            _path = save_open_deed(_deed_record)
            set_deed_record(_deed_record)
            mo.status.toast(f"saved {_path.name}")

    # Blank ones are saved too: close then says which.
    save_fields_btn = mo.ui.button(
        label="save header fields",
        disabled=_open is None,
        on_click=_save_header_fields,
    )
    save_header_btn = mo.ui.button(
        label="save box as header",
        # Not with pending boxes: the drawn box is then the item's next one.
        disabled=_open is None
        or _locked
        or drawn_box is None
        or bool(get_pending_boxes())
        or _names.index(page.name) < _names.index(_open["scans"][0]),
        on_click=_save_header_box,
    )
    header_dd = mo.ui.dropdown(options=_tags)
    # The later ones move up: H2 becomes H1.
    delete_header_btn = mo.ui.button(
        label="delete header box",
        disabled=not _tags or _locked,
        on_click=_delete_header_box,
    )
    return delete_header_btn, header_dd, save_fields_btn, save_header_btn


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
    # Like the jump's go: a deed never crosses books, pending boxes belong to this page.
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
        label="go to deed",
        disabled=_disabled,
        on_click=lambda _: set_book_page(
            lambda book_page: (book_page[0], _read_picked_file()[1])
        ),
    )

    def _reopen(_):
        # The picked deed is open again, as if never closed: save, delete and
        # close then rewrite its file.
        _deed_record, _first_scan_i = _read_picked_file()
        set_deed_id(deed_dd.value)
        set_deed_record(_deed_record)
        set_type(None)
        set_book_page(lambda book_page: (book_page[0], _first_scan_i))

    # Disabled like go; an edit needs an open deed, so that is covered too.
    reopen_btn = mo.ui.button(
        label="reopen", disabled=_disabled, on_click=_reopen
    )

    def _delete_file(_):
        _path = deed_path(book, deed_dd.value)
        _path.unlink()
        mo.status.toast(f"deleted {_path.name}")
        # Still None: this rebuilds the dropdown, the faded boxes and the debug pane.
        set_deed_record(None)

    # Two steps: delete deed, then confirm or cancel. Picking another deed shows
    # delete deed again.
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
            label="delete deed",
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
    # The deed to move the open deed's annotation to: one without a file. Re-created
    # (cleared) on every open, write and close, so the deeds with a file are up to date.
    get_deed_record()
    move_dd = mo.ui.dropdown(
        options={
            _choice: _deed_id
            for _choice, _deed_id in deed_choices(deeds, book).items()
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
    copied_deed_person_data,
    deed_path,
    deeds,
    get_deed_record,
    get_editing,
    get_pending_boxes,
    mo,
    move_dd,
    move_deed_record,
    set_deed_id,
    set_deed_record,
):
    # Moves the open deed's annotation to the picked deed. Locked as close deed, but on
    # any page: a move does not depend on the page.
    # It stays open, under the new deed; its old deed has no file again.
    def _move(_):
        try:
            _deed = deeds[move_dd.value]
            _deed_record = move_deed_record(
                get_deed_record(),
                old_path=deed_path(book, get_deed_record()["deed_id"]),
                new_path=deed_path(book, _deed["deed_id"]),
                deed_id=_deed["deed_id"],
                copied_deed_person_data=copied_deed_person_data(_deed),
                annotator_name=annotator_name,
            )
        # The deed cannot be used, or another tab opened it meanwhile.
        except ValueError as _e:
            mo.status.toast(str(_e))
            return
        set_deed_id(_deed_record["deed_id"])
        set_deed_record(_deed_record)
        mo.status.toast(
            f"saved {deed_path(book, _deed_record['deed_id']).name}, annotation moved"
        )

    move_btn = mo.ui.button(
        label="move annotation",
        disabled=move_dd.value is None
        or bool(get_pending_boxes())
        or get_editing() is not None,
        on_click=_move,
    )
    # Only while a deed is open: there is no annotation to move otherwise.
    move_ui = (
        mo.hstack([move_dd, move_btn], justify="start", align="end")
        if get_deed_record() is not None
        else mo.md("")
    )
    return (move_ui,)


@app.cell(hide_code=True)
def balance_inputs(get_deed_record, mo):
    # The balance's totals, editable while a deed is open and showing its saved values (a
    # typo check). Re-created on every open, write and close: totals typed but not saved
    # are then gone.
    _open = get_deed_record()
    _balance = _open["annotation"]["balance"] if _open else {}
    # debounce=False: the value is in before a click on save balance totals, as for the
    # item amount
    total_assets_in, total_liabilities_in, total_in = (
        mo.ui.text(
            label=_field.replace("_", " "),
            value=_balance.get(_field, ""),
            disabled=_open is None,
            debounce=False,
        )
        for _field in ["total_assets", "total_liabilities", "total"]
    )
    return total_assets_in, total_in, total_liabilities_in


@app.cell(hide_code=True)
def balance_buttons(
    add_balance_box,
    deed_boxes,
    delete_balance_box,
    drawn_box,
    get_deed_record,
    get_editing,
    get_pending_boxes,
    mo,
    page,
    pages,
    save_open_deed,
    set_balance_totals,
    set_deed_record,
    total_assets_in,
    total_in,
    total_liabilities_in,
):
    # The totals and the boxes are saved apart, and either may be blank or none: close
    # checks neither. Boxes go in one at a time, like the header's, on the deed's first scan
    # or a later one: before it they would be outside scans. Each has its own tag: B1, B2…
    _open = get_deed_record()
    _names = [p.name for p in pages]
    _tags = {
        f"{_tag} · page {_names.index(_box['scan']) + 1}": _tag
        for _tag, _box in deed_boxes(_open)
        if _tag[0] == "B"
    }
    # Editing an item locks the boxes, as for the header.
    _locked = get_editing() is not None

    def _write(_deed_record):
        _path = save_open_deed(_deed_record)
        set_deed_record(_deed_record)
        mo.status.toast(f"saved {_path.name}")

    def _delete_balance_box(_):
        if balance_dd.value:
            _write(delete_balance_box(get_deed_record(), balance_dd.value))

    save_totals_btn = mo.ui.button(
        label="save balance totals",
        disabled=_open is None,
        on_click=lambda _: _write(
            set_balance_totals(
                get_deed_record(),
                total_assets_in.value,
                total_liabilities_in.value,
                total_in.value,
            )
        ),
    )
    save_balance_btn = mo.ui.button(
        label="save box as balance",
        # Not with pending boxes: the drawn box is then the item's next one.
        disabled=_open is None
        or _locked
        or drawn_box is None
        or bool(get_pending_boxes())
        or _names.index(page.name) < _names.index(_open["scans"][0]),
        on_click=lambda _: _write(
            add_balance_box(get_deed_record(), page.name, drawn_box)
        ),
    )
    balance_dd = mo.ui.dropdown(options=_tags)
    # The later ones move up: B2 becomes B1.
    delete_balance_btn = mo.ui.button(
        label="delete balance box",
        disabled=not _tags or _locked,
        on_click=_delete_balance_box,
    )
    return balance_dd, delete_balance_btn, save_balance_btn, save_totals_btn


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
    get_deed_record,
    get_editing,
    get_pending_boxes,
    mo,
    page,
    page_i,
    pages,
    status_text,
):
    # Its own cell, not in `layout`: a click reruns `layout` at once (it shows the buttons), with
    # the new state but the old elements. This cell reruns only with the rebuilt elements, so
    # the status line never says "no deed" while the old deed dropdown is still showing.
    status_line = mo.md(
        status_text(
            book,
            page,
            page_i,
            len(pages),
            get_deed_record(),
            len(get_pending_boxes()),
            get_editing(),
        )
    )
    return (status_line,)


@app.cell(hide_code=True)
def layout(
    amount_in,
    annotator_row,
    balance_dd,
    book,
    book_dd,
    cancel_edit_btn,
    category_in,
    clear_pending_btn,
    close_deed_btn,
    continue_btn,
    date_of_death_in,
    debug_switch,
    deed_details,
    deed_path,
    deed_row,
    delete_balance_btn,
    delete_btn,
    delete_file_ui,
    delete_header_btn,
    desc_in,
    edit_btn,
    fig_h_slider,
    full_name_in,
    get_deed_id,
    go_to_btn,
    header_dd,
    item_dd,
    mo,
    move_ui,
    next_page_btn,
    open_btn,
    open_hint,
    page_view,
    place_of_residence_in,
    prev_page_btn,
    quality_slider,
    reopen_btn,
    save_balance_btn,
    save_btn,
    save_fields_btn,
    save_header_btn,
    save_totals_btn,
    status_line,
    total_assets_in,
    total_in,
    total_liabilities_in,
    type_radio,
    zooms,
):
    _page_column = mo.vstack(
        [page_view, mo.hstack([quality_slider, fig_h_slider], justify="start")]
    )
    # Top to bottom, from the widest scope to the narrowest, split by rules: annotator, book
    # and deed, header, balance, page, item.
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
                    close_deed_btn,
                ],
                justify="start",
            ),
            mo.md("---"),
            mo.hstack(
                [
                    full_name_in,
                    date_of_death_in,
                    place_of_residence_in,
                    save_fields_btn,
                ],
                justify="start",
                align="end",
            ),
            mo.hstack(
                [save_header_btn, header_dd, delete_header_btn],
                justify="start",
            ),
            mo.md("---"),
            mo.hstack(
                [
                    total_assets_in,
                    total_liabilities_in,
                    total_in,
                    save_totals_btn,
                ],
                justify="start",
                align="end",
            ),
            mo.hstack(
                [save_balance_btn, balance_dd, delete_balance_btn],
                justify="start",
            ),
            mo.md("---"),
            mo.hstack([prev_page_btn, next_page_btn], justify="start"),
            mo.md("---"),
            mo.hstack([type_radio, category_in, amount_in], justify="start"),
            desc_in,
            mo.hstack(
                [continue_btn, clear_pending_btn, save_btn], justify="start"
            ),
            mo.hstack(
                [item_dd, edit_btn, cancel_edit_btn, delete_btn],
                justify="start",
            ),
        ]
    )
    # `-- --debug`, switch on: the open (or last closed) deed's file right of the form.
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
                        mo.md(
                            f"```json\n{_path.read_text(encoding='utf-8')}\n```"
                        )
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
    # Every page of every book in annotating order: the slider position is overall progress.
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
    marimo_ui,
    mo,
    set_book_page,
):
    _i = jump_slider.value - 1
    _target = all_pages[_i]
    _here = get_book_page()
    # A deed never crosses books, and pending boxes belong to this page: while a deed is
    # open or boxes are pending, the slider and strip are view only.
    jump_btn = mo.ui.button(
        label="go",
        disabled=get_deed_record() is not None
        or bool(get_pending_boxes())
        or _target == _here,
        on_click=lambda _: set_book_page(_target),
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
            marimo_ui.thumbnail_strip(books, book_pages, _here, _i),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
