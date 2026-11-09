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
        close_deed_record,
        deed_boxes,
        deed_path,
        delete_balance_box,
        delete_header_box,
        item_tags,
        list_pages,
        load_deed_records,
        save_deed_record,
        saved_boxes,
        set_balance_totals,
        set_header_fields,
    )
    from vox_paginae.single_deed_input import (
        deed_choices,
        find_single_deed_folders,
        input_item_choices,
        load_single_deed_input,
        new_deed_record_from_input,
    )
    from vox_paginae.ui import (
        draw_scan,
        scan_for_display,
        selection_box,
        status_text,
    )

    return (
        Path,
        add_balance_box,
        add_header_box,
        close_deed_record,
        deed_boxes,
        deed_choices,
        deed_path,
        delete_balance_box,
        delete_header_box,
        draw_scan,
        find_single_deed_folders,
        input_item_choices,
        item_tags,
        list_pages,
        load_deed_records,
        load_single_deed_input,
        marimo_ui,
        mo,
        new_deed_record_from_input,
        save_deed_record,
        saved_boxes,
        scan_for_display,
        selection_box,
        set_balance_totals,
        set_header_fields,
        status_text,
    )


@app.cell
def _(Path, marimo_ui, mo):
    # `marimo edit|run notebooks/single_deed_annotation.py -- --data-root <dir>` overrides
    # the default.
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
    # "" until locked: nothing past the folder cell runs. From the state, not the input,
    # so typing reruns nothing below.
    annotator_name = _name if _locked else ""
    return annotator_in, annotator_name


@app.cell(hide_code=True)
def annotator_lock(annotator_in, get_annotator, marimo_ui, set_annotator):
    annotator_row = marimo_ui.annotator_row(
        annotator_in, get_annotator, set_annotator
    )
    return (annotator_row,)


@app.cell(hide_code=True)
def session_state(find_single_deed_folders, mo, root):
    folders = find_single_deed_folders(root)
    # Everything below resets when the root changes.
    # (folder, scan index) of the picked deed; None until one is picked.
    get_folder_scan, set_folder_scan = mo.state(None)
    # None = no deed open: one is opened with the open button.
    get_deed_record, set_deed_record = mo.state(None)
    # The open deed's single deed input, set on open. Apart from `single_deed_input`, which
    # is re-read on every page turn: the input item pick must survive one.
    get_open_deed_input, set_open_deed_input = mo.state(None)
    get_pending_boxes, set_pending_boxes = mo.state(
        []
    )  # (scan, bbox) pending boxes of the item being drawn
    # Tag ("A2") of the item loaded by edit: save replaces it. None = save adds an item.
    get_editing, set_editing = mo.state(None)
    # Type to prefill the radio with. Set only on edit and close, so a save keeps the last
    # type used without rebuilding the radio.
    get_type, set_type = mo.state(None)
    return (
        folders,
        get_deed_record,
        get_editing,
        get_folder_scan,
        get_open_deed_input,
        get_pending_boxes,
        get_type,
        set_deed_record,
        set_editing,
        set_folder_scan,
        set_open_deed_input,
        set_pending_boxes,
        set_type,
    )


@app.cell(hide_code=True)
def deed_picker(
    deed_choices,
    folders,
    get_deed_record,
    get_folder_scan,
    get_pending_boxes,
    mo,
    set_folder_scan,
):
    # Picking a deed shows its folder's first scan and writes nothing. Locked while a deed
    # is open, and while boxes are pending: they belong to this scan. Re-created on every
    # open, write and close, so the labels of deeds with a file are up to date.
    get_deed_record()
    try:
        _choices = deed_choices(folders)
        deed_choices_error = None
    except ValueError as _e:  # one input without ref_reg: no deed can be listed
        _choices, deed_choices_error = {}, mo.callout(mo.md(str(_e)), kind="danger")
    _picked = get_folder_scan()[0] if get_folder_scan() else None
    deed_dd = mo.ui.dropdown(
        options=_choices,
        value=next((k for k, f in _choices.items() if f == _picked), None),
        searchable=True,
        label="deed",
        disabled=get_deed_record() is not None or bool(get_pending_boxes()),
        on_change=lambda folder: set_folder_scan((folder, 0)),
    )
    return deed_choices_error, deed_dd


@app.cell(hide_code=True)
def type_input(get_type, mo):
    type_radio = mo.ui.radio(
        options=["assets", "liabilities"], value=get_type(), inline=True
    )
    return (type_radio,)


@app.cell(hide_code=True)
def _(get_deed_record, get_editing, input_item_dd, item_tags, mo):
    get_deed_record()  # re-created (cleared) after every open, write and close
    # Prefilled from the picked input item, else from the item being edited, if any. The
    # input has no category: it stays the edited item's.
    _edited = dict(item_tags(get_deed_record())).get(get_editing(), {})
    _item = input_item_dd.value or _edited
    category_in = mo.ui.text(
        label="category", value=_edited.get("category") or ""
    )
    # debounce=False: save enables while typing (#11).
    amount_in = mo.ui.text(
        label="amount", value=_item.get("amount", ""), debounce=False
    )
    desc_in = mo.ui.text_area(
        label="description",
        value=_item.get("description", ""),
        full_width=True,
        debounce=False,
        rows=3,  # it can be dragged taller
    )
    return amount_in, category_in, desc_in


@app.cell(hide_code=True)
def _(
    annotator_name,
    annotator_row,
    deed_choices_error,
    deed_dd,
    get_folder_scan,
    list_pages,
    load_single_deed_input,
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
    mo.stop(
        deed_choices_error is not None,
        mo.vstack([annotator_row, deed_choices_error]),
    )
    mo.stop(
        get_folder_scan() is None,
        mo.vstack([annotator_row, deed_dd, mo.md("**pick a deed to see its pages**")]),
    )
    folder, scan_i = get_folder_scan()
    scans = list_pages(folder)
    mo.stop(
        not scans,
        mo.vstack(
            [
                annotator_row,
                deed_dd,
                mo.md(f"**no `*.jpg` in folder `{folder.relative_to(root)}`**"),
            ]
        ),
    )
    single_deed_input = load_single_deed_input(folder)
    scan = scans[scan_i]
    return folder, scan, scan_i, scans, single_deed_input


@app.cell(hide_code=True)
def deed_save(
    annotator_name,
    deed_path,
    folder,
    mo,
    new_deed_record_from_input,
    save_deed_record,
    set_deed_record,
    set_open_deed_input,
):
    # Every write goes to the open deed's own file, by the locked annotator.
    def save_open_deed(deed_record):
        return save_deed_record(
            deed_path(folder, deed_record["deed_id"]),
            deed_record,
            annotator_name,
        )

    def save_and_show_open_deed(deed_record):
        path = save_open_deed(deed_record)
        set_deed_record(deed_record)
        mo.status.toast(f"saved {path.name}")

    def open_new_deed(deed_folder, single_deed_input, first_scan):
        # Its file is written at once: one file per deed.
        deed_record = new_deed_record_from_input(single_deed_input, first_scan)
        path = save_deed_record(
            deed_path(deed_folder, deed_record["deed_id"]),
            deed_record,
            annotator_name,
        )
        set_deed_record(deed_record)
        set_open_deed_input(single_deed_input)
        return path

    return open_new_deed, save_and_show_open_deed, save_open_deed


@app.cell(hide_code=True)
def page_buttons(
    close_deed_record,
    deed_path,
    folder,
    folders,
    get_deed_record,
    get_editing,
    get_pending_boxes,
    list_pages,
    load_single_deed_input,
    mo,
    open_new_deed,
    save_open_deed,
    scan,
    scan_i,
    scans,
    set_deed_record,
    set_folder_scan,
    set_type,
):
    _last_scan = scan_i == len(scans) - 1
    # The deed after this one, in the deed dropdown's order; None on the last deed.
    _next_folder = next(iter(folders[folders.index(folder) + 1 :]), None)

    def _next_page(_):
        if not _last_scan:
            set_folder_scan((folder, scan_i + 1))
            return
        # Past the last scan: the open deed, if any, closes, and the next deed opens on
        # its first scan. A next deed with a file is only picked, as is any next deed
        # when no deed is open.
        if get_deed_record() is not None:
            # Read before the close: an error here leaves the deed open.
            next_input = load_single_deed_input(_next_folder)
            next_scans = list_pages(_next_folder)
            try:
                closed = close_deed_record(
                    get_deed_record(), [p.name for p in scans], scan.name
                )
            except ValueError as e:
                # No header box or a blank field: it stays open, here.
                mo.status.toast(str(e))
                return
            path = save_open_deed(closed)
            set_deed_record(None)
            set_type(None)
            mo.status.toast(f"saved {path.name}, deed closed")
            # Checked at click, as in open: another tab may have written it meanwhile.
            if (
                next_scans
                and not deed_path(_next_folder, next_input["ref_reg"]).exists()
            ):
                path = open_new_deed(
                    _next_folder, next_input, next_scans[0].name
                )
                mo.status.toast(f"saved {path.name}, deed open")
        set_folder_scan((_next_folder, 0))

    next_page_btn = mo.ui.button(
        label="next page",
        # Not past the last deed. Pending boxes and an item being edited belong to this
        # deed: they stop it here, as they stop close deed.
        disabled=_last_scan
        and (
            _next_folder is None
            or bool(get_pending_boxes())
            or get_editing() is not None
        ),
        on_click=_next_page,
    )
    prev_page_btn = mo.ui.button(
        label="prev page",
        disabled=scan_i == 0,
        on_click=lambda _: set_folder_scan((folder, scan_i - 1)),
    )
    return next_page_btn, prev_page_btn


@app.cell(hide_code=True)
def view_sliders(marimo_ui):
    quality_slider, fig_h_slider = marimo_ui.view_sliders()
    return fig_h_slider, quality_slider


@app.cell(hide_code=True)
def _(fig_h_slider, quality_slider, scan, scan_for_display):
    scan_pixels, scan_size, png_dpi = scan_for_display(
        scan, fig_h_slider.value, quality_slider.value
    )
    return png_dpi, scan_pixels, scan_size


@app.cell(hide_code=True, expand_output=True)
def _(
    deed_boxes,
    draw_scan,
    fig_h_slider,
    folder,
    get_deed_record,
    get_pending_boxes,
    marimo_ui,
    png_dpi,
    saved_boxes,
    scan,
    scan_pixels,
    scan_size,
):
    FIG_H = fig_h_slider.value  # inches, shown at 100 px each

    # The closed deed's saved boxes, faded; the open deed's, tagged.
    _open = get_deed_record()
    _ax = draw_scan(
        scan_pixels,
        scan_size,
        FIG_H,
        png_dpi,
        saved=saved_boxes(folder, scan.name, _open["deed_id"] if _open else None),
        deed=[
            (_tag, _box["bbox"])
            for _tag, _box in deed_boxes(_open)
            if _box["scan"] == scan.name
        ],
        pending=[
            _bbox for _scan, _bbox in get_pending_boxes() if _scan == scan.name
        ],
    )

    page_sel, page_view = marimo_ui.page_view(_ax, scan_size, FIG_H)
    return page_sel, page_view


@app.cell(hide_code=True)
def _(get_pending_boxes, page_sel, scan, selection_box):
    drawn_box = selection_box(page_sel.value)

    # The unsaved item, in draw order: pending boxes, then the one drawn now.
    layout_boxes = get_pending_boxes() + (
        [(scan.name, drawn_box)] if drawn_box else []
    )
    return drawn_box, layout_boxes


@app.cell(hide_code=True)
def zooms(folder, layout_boxes, marimo_ui):
    # The unsaved item at full resolution, in draw order, to read while transcribing.
    zooms = marimo_ui.zooms(folder, layout_boxes)
    return (zooms,)


@app.cell(hide_code=True)
def item_dropdown(get_deed_record, marimo_ui):
    # Apart from the item inputs: typing there would rebuild it and lose the pick (#60).
    item_dd = marimo_ui.item_dropdown(get_deed_record())
    return (item_dd,)


@app.cell(hide_code=True)
def input_item_dropdown(
    get_deed_record,
    get_editing,
    get_open_deed_input,
    input_item_choices,
    mo,
    set_type,
):
    # Fills in the item inputs, so in a cell of its own: typing there would rebuild it
    # and lose the pick (#60). Re-created (cleared) on every write, edit and cancel.
    get_editing()
    _choices = (
        input_item_choices(get_open_deed_input(), get_deed_record())
        if get_deed_record() is not None
        else {}
    )
    input_item_dd = mo.ui.dropdown(
        options=_choices,
        label="input item",
        disabled=not _choices,
        # The radio is re-created with the picked type; the inputs read the pick below.
        on_change=lambda item: set_type(item["type"]) if item else None,
    )
    return (input_item_dd,)


@app.cell(hide_code=True)
def item_buttons(
    amount_in,
    category_in,
    desc_in,
    drawn_box,
    get_deed_record,
    get_editing,
    get_pending_boxes,
    item_dd,
    layout_boxes,
    marimo_ui,
    save_and_show_open_deed,
    save_open_deed,
    scan,
    scans,
    set_deed_record,
    set_editing,
    set_pending_boxes,
    set_type,
    type_radio,
):
    (
        continue_btn,
        clear_pending_btn,
        save_btn,
        edit_btn,
        cancel_edit_btn,
        delete_btn,
        close_deed_btn,
    ) = marimo_ui.item_buttons(
        item_dd,
        type_radio=type_radio,
        category_in=category_in,
        amount_in=amount_in,
        desc_in=desc_in,
        get_deed_record=get_deed_record,
        set_deed_record=set_deed_record,
        save_open_deed=save_open_deed,
        save_and_show_open_deed=save_and_show_open_deed,
        get_pending_boxes=get_pending_boxes,
        set_pending_boxes=set_pending_boxes,
        get_editing=get_editing,
        set_editing=set_editing,
        set_type=set_type,
        scan_names=[p.name for p in scans],
        scan_name=scan.name,
        drawn_box=drawn_box,
        layout_boxes=layout_boxes,
    )
    return (
        cancel_edit_btn,
        clear_pending_btn,
        close_deed_btn,
        continue_btn,
        delete_btn,
        edit_btn,
        save_btn,
    )


@app.cell(hide_code=True)
def deed_open(
    deed_path,
    drawn_box,
    folder,
    get_deed_record,
    get_pending_boxes,
    load_deed_records,
    mo,
    open_new_deed,
    scan,
    scans,
    set_deed_record,
    set_folder_scan,
    set_open_deed_input,
    set_type,
    single_deed_input,
):
    _ref_reg = single_deed_input["ref_reg"]

    def _open(_):
        # Checked at click: another tab (its own session) may have written it meanwhile.
        if deed_path(folder, _ref_reg).exists():
            # Open again, as if never closed, on its first scan: the next writes rewrite
            # its file.
            _deed_record = load_deed_records(folder)[_ref_reg]
            set_deed_record(_deed_record)
            set_open_deed_input(single_deed_input)
            set_type(None)
            set_folder_scan(
                (
                    folder,
                    [p.name for p in scans].index(_deed_record["scans"][0]),
                )
            )
            return
        # This scan is its first scan.
        _path = open_new_deed(folder, single_deed_input, scan.name)
        mo.status.toast(f"saved {_path.name}, deed open")

    # Opens the picked deed, or reopens it if it has a file. Not with pending boxes: a
    # reopen can change the scan.
    open_btn = mo.ui.button(
        label="open",
        disabled=get_deed_record() is not None or bool(get_pending_boxes()),
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
def header_inputs(get_deed_record, marimo_ui):
    # Editable while a deed is open: pre-filled on open from the deed's copied data.
    full_name_in, date_of_death_in, place_of_residence_in = (
        marimo_ui.section_field_inputs(
            get_deed_record(),
            "header",
            ["full_name", "date_of_death", "place_of_residence"],
        )
    )
    return date_of_death_in, full_name_in, place_of_residence_in


@app.cell(hide_code=True)
def header_buttons(
    add_header_box,
    date_of_death_in,
    delete_header_box,
    drawn_box,
    full_name_in,
    get_deed_record,
    get_editing,
    get_pending_boxes,
    marimo_ui,
    place_of_residence_in,
    save_and_show_open_deed,
    scan,
    scans,
    set_header_fields,
):
    # Blank fields are saved too: close then says which.
    save_fields_btn, save_header_btn, header_dd, delete_header_btn = (
        marimo_ui.section_buttons(
            "header",
            (full_name_in, date_of_death_in, place_of_residence_in),
            save_fields_label="save header fields",
            set_fields=set_header_fields,
            add_box=add_header_box,
            delete_box=delete_header_box,
            get_deed_record=get_deed_record,
            save_and_show_open_deed=save_and_show_open_deed,
            scan_names=[p.name for p in scans],
            scan_name=scan.name,
            drawn_box=drawn_box,
            has_pending_boxes=bool(get_pending_boxes()),
            editing_item=get_editing() is not None,
        )
    )
    return delete_header_btn, header_dd, save_fields_btn, save_header_btn


@app.cell(hide_code=True)
def balance_inputs(get_deed_record, marimo_ui):
    total_assets_in, total_liabilities_in, total_in = (
        marimo_ui.section_field_inputs(
            get_deed_record(),
            "balance",
            ["total_assets", "total_liabilities", "total"],
        )
    )
    return total_assets_in, total_in, total_liabilities_in


@app.cell(hide_code=True)
def balance_buttons(
    add_balance_box,
    delete_balance_box,
    drawn_box,
    get_deed_record,
    get_editing,
    get_pending_boxes,
    marimo_ui,
    save_and_show_open_deed,
    scan,
    scans,
    set_balance_totals,
    total_assets_in,
    total_in,
    total_liabilities_in,
):
    # The totals and the boxes are saved apart, and either may be blank or none.
    save_totals_btn, save_balance_btn, balance_dd, delete_balance_btn = (
        marimo_ui.section_buttons(
            "balance",
            (total_assets_in, total_liabilities_in, total_in),
            save_fields_label="save balance totals",
            set_fields=set_balance_totals,
            add_box=add_balance_box,
            delete_box=delete_balance_box,
            get_deed_record=get_deed_record,
            save_and_show_open_deed=save_and_show_open_deed,
            scan_names=[p.name for p in scans],
            scan_name=scan.name,
            drawn_box=drawn_box,
            has_pending_boxes=bool(get_pending_boxes()),
            editing_item=get_editing() is not None,
        )
    )
    return balance_dd, delete_balance_btn, save_balance_btn, save_totals_btn


@app.cell(hide_code=True)
def status_line(
    folder,
    get_deed_record,
    get_editing,
    get_pending_boxes,
    mo,
    scan,
    scan_i,
    scans,
    status_text,
):
    # Its own cell, not in `layout`: see the book notebook's status_line.
    status_line = mo.md(
        status_text(
            folder,
            scan,
            scan_i,
            len(scans),
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
    cancel_edit_btn,
    category_in,
    clear_pending_btn,
    close_deed_btn,
    continue_btn,
    date_of_death_in,
    deed_dd,
    delete_balance_btn,
    delete_btn,
    delete_header_btn,
    desc_in,
    edit_btn,
    fig_h_slider,
    full_name_in,
    header_dd,
    input_item_dd,
    item_dd,
    mo,
    next_page_btn,
    open_btn,
    open_hint,
    page_view,
    place_of_residence_in,
    prev_page_btn,
    quality_slider,
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
    # Top to bottom, from the widest scope to the narrowest, split by rules: annotator and
    # deed, header, balance, page, item.
    _form = mo.vstack(
        [
            annotator_row,
            status_line,
            mo.hstack(
                [deed_dd, open_btn, close_deed_btn],
                justify="start",
                align="end",
            ),
            open_hint,
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
            input_item_dd,
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
    # Page at its fixed size on the left; form and zooms take the rest of the width.
    # None = no flex: a 0 would let the page column shrink to nothing.
    mo.hstack(
        [_page_column, mo.vstack([_form, zooms])],
        widths=[None, 1],
        align="start",
    )
    return


if __name__ == "__main__":
    app.run()
