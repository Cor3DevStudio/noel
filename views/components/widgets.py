"""Reusable UI components."""

import customtkinter as ctk
from typing import Callable, Optional

from views.components.theme import Theme


class StatCard(ctk.CTkFrame):
    """Metric card with colored icon badge and accent strip."""

    def __init__(
        self,
        master,
        title: str,
        value: str,
        icon: str = "",
        color: str = Theme.ACCENT,
        bg_tint: str = Theme.ACCENT_LIGHT,
        compact: bool = False,
        **kwargs,
    ):
        super().__init__(
            master,
            fg_color=Theme.CARD_BG,
            corner_radius=10 if compact else Theme.CORNER_RADIUS,
            border_width=1,
            border_color=Theme.BORDER,
            **kwargs,
        )

        if compact:
            pad = 8
            icon_size = 28
            icon_font = 13
            value_font = ("Segoe UI", 15, "bold")
            title_font = Theme.FONT_TINY
            self.configure(height=68)
            self.pack_propagate(False)
            self.grid_propagate(False)
        else:
            pad = 14
            icon_size = 48
            icon_font = 20
            value_font = ("Segoe UI", 26, "bold")
            title_font = Theme.FONT_SMALL

        accent = ctk.CTkFrame(self, fg_color=color, width=3 if compact else 4, corner_radius=0)
        accent.pack(side="left", fill="y")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(side="left", fill="both", expand=True, padx=(pad, pad), pady=pad)

        icon_frame = ctk.CTkFrame(
            body, fg_color=bg_tint, width=icon_size, height=icon_size,
            corner_radius=6 if compact else 10,
        )
        icon_frame.pack(side="left", padx=(0, 8 if compact else 10))
        icon_frame.pack_propagate(False)
        ctk.CTkLabel(icon_frame, text=icon, font=("Segoe UI Emoji", icon_font)).place(
            relx=0.5, rely=0.5, anchor="center"
        )

        text_frame = ctk.CTkFrame(body, fg_color="transparent")
        text_frame.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            text_frame, text=title, font=title_font,
            text_color=Theme.TEXT_SECONDARY, anchor="w",
        ).pack(fill="x")
        self.value_label = ctk.CTkLabel(
            text_frame, text=value, font=value_font,
            text_color=color, anchor="w",
        )
        self.value_label.pack(fill="x", anchor="w", pady=(0 if compact else 2, 0))

    def set_value(self, value: str) -> None:
        self.value_label.configure(text=value)


class QuickActionButton(ctk.CTkButton):
    def __init__(
        self, master, text: str, icon: str, color: str, hover: str, command=None, **kwargs
    ):
        super().__init__(
            master,
            text=f"  {icon}   {text}",
            anchor="w",
            height=38,
            font=Theme.FONT_SMALL,
            fg_color=Theme.PRIMARY,
            text_color=Theme.TEXT_PRIMARY,
            hover_color=Theme.SECONDARY,
            border_width=1,
            border_color=Theme.BORDER,
            corner_radius=Theme.BUTTON_RADIUS,
            command=command,
            **kwargs,
        )


class PanelCard(ctk.CTkFrame):
    """White panel with title bar."""

    def __init__(self, master, title: str, subtitle: str = "", **kwargs):
        super().__init__(
            master,
            fg_color=Theme.CARD_BG,
            corner_radius=Theme.CORNER_RADIUS,
            border_width=1,
            border_color=Theme.BORDER,
            **kwargs,
        )
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header, text=title, font=Theme.FONT_SUBHEADING, text_color=Theme.TEXT_PRIMARY, anchor="w",
        ).grid(row=0, column=0, sticky="w")
        if subtitle:
            ctk.CTkLabel(
                header, text=subtitle, font=Theme.FONT_TINY, text_color=Theme.TEXT_MUTED, anchor="w",
            ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 12))
        self.body.grid_columnconfigure(0, weight=1)
        self.body.grid_rowconfigure(0, weight=1)


class PageHeader(ctk.CTkFrame):
    def __init__(self, master, title: str, subtitle: str = "", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text=title, font=Theme.FONT_TITLE, text_color=Theme.TEXT_PRIMARY).grid(
            row=0, column=0, sticky="w"
        )
        if subtitle:
            ctk.CTkLabel(
                self, text=subtitle, font=Theme.FONT_BODY, text_color=Theme.TEXT_SECONDARY
            ).grid(row=1, column=0, sticky="w", pady=(4, 0))


class SearchBar(ctk.CTkFrame):
    def __init__(self, master, placeholder: str = "Search...", on_search: Optional[Callable] = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_search = on_search
        self.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(
            self, placeholder_text=placeholder, height=42,
            corner_radius=Theme.BUTTON_RADIUS, font=Theme.FONT_BODY,
            border_color=Theme.BORDER,
        )
        self.entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.entry.bind("<Return>", lambda e: self._trigger())

        ctk.CTkButton(
            self, text="Search", width=100, height=42,
            corner_radius=Theme.BUTTON_RADIUS, font=Theme.FONT_BUTTON,
            fg_color=Theme.ACCENT, hover_color=Theme.ACCENT_HOVER,
            command=self._trigger,
        ).grid(row=0, column=1)

    def _trigger(self) -> None:
        if self.on_search:
            self.on_search(self.entry.get())

    def get(self) -> str:
        return self.entry.get()

    def clear(self) -> None:
        self.entry.delete(0, "end")


class DataTable(ctk.CTkScrollableFrame):
    _CELL_PADX = 12
    _CELL_PADY_HEAD = 10
    _CELL_PADY_BODY = 8

    def __init__(self, master, columns: list, **kwargs):
        super().__init__(
            master, fg_color=Theme.CARD_BG, corner_radius=Theme.CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER, **kwargs
        )
        self.columns = columns
        self._row_cells: list[list[ctk.CTkFrame]] = []
        self._row_values: list = []
        self._selected_index: Optional[int] = None
        self._next_row = 1

        self._body = ctk.CTkFrame(self, fg_color="transparent")
        self._body.pack(fill="both", expand=True, padx=2, pady=2)
        for i in range(len(columns)):
            self._body.grid_columnconfigure(i, weight=1, uniform="dt_cols")
        self._build_header()

    def _build_header(self) -> None:
        last_col = len(self.columns) - 1
        for i, col in enumerate(self.columns):
            cell = ctk.CTkFrame(self._body, fg_color=Theme.SECONDARY, corner_radius=0)
            cell.grid(
                row=0, column=i, sticky="nsew",
                padx=(0, 1) if i < last_col else 0, pady=(0, 1),
            )
            ctk.CTkLabel(
                cell, text=col, font=Theme.FONT_SUBHEADING,
                text_color=Theme.TEXT_PRIMARY, anchor="w",
            ).pack(fill="x", padx=self._CELL_PADX, pady=self._CELL_PADY_HEAD)

    def clear_rows(self) -> None:
        for cells in self._row_cells:
            for cell in cells:
                cell.destroy()
        self._row_cells.clear()
        self._row_values.clear()
        self._selected_index = None
        self._next_row = 1

    def _select_row(self, index: int) -> None:
        for i, cells in enumerate(self._row_cells):
            color = Theme.ACCENT_LIGHT if i == index else "transparent"
            for cell in cells:
                cell.configure(fg_color=color)
        self._selected_index = index

    def get_selected_row(self) -> Optional[list]:
        if self._selected_index is not None and self._selected_index < len(self._row_values):
            return self._row_values[self._selected_index]
        return None

    def _bind_row_click(self, widgets, index: int, on_click: Optional[Callable]) -> None:
        for widget in widgets:
            widget.bind("<Button-1>", lambda e, idx=index: self._select_row(idx))
            widget.configure(cursor="hand2")
            if on_click:
                widget.bind("<Double-Button-1>", lambda e, fn=on_click: fn())

    def add_row(self, values: list, on_click: Optional[Callable] = None) -> None:
        index = len(self._row_cells)
        row_num = self._next_row
        self._next_row += 1
        last_col = len(self.columns) - 1
        cells: list[ctk.CTkFrame] = []

        for i in range(len(self.columns)):
            val = values[i] if i < len(values) else ""
            cell = ctk.CTkFrame(self._body, fg_color="transparent", corner_radius=0)
            cell.grid(
                row=row_num, column=i, sticky="nsew",
                padx=(0, 1) if i < last_col else 0, pady=1,
            )
            lbl = ctk.CTkLabel(
                cell, text=str(val), font=Theme.FONT_BODY,
                text_color=Theme.TEXT_PRIMARY, anchor="w",
            )
            lbl.pack(fill="x", padx=self._CELL_PADX, pady=self._CELL_PADY_BODY)
            self._bind_row_click((cell, lbl), index, on_click)
            cells.append(cell)

        self._row_cells.append(cells)
        self._row_values.append(list(values))


class FormField(ctk.CTkFrame):
    def __init__(self, master, label: str, widget_type: str = "entry", values: list = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text=label, font=Theme.FONT_BODY, text_color=Theme.TEXT_SECONDARY, anchor="w").grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )
        if widget_type == "entry":
            self.widget = ctk.CTkEntry(self, height=38, corner_radius=Theme.BUTTON_RADIUS, font=Theme.FONT_BODY)
        elif widget_type == "combo":
            self.widget = ctk.CTkComboBox(
                self, values=values or [], height=38,
                corner_radius=Theme.BUTTON_RADIUS, font=Theme.FONT_BODY,
            )
        elif widget_type == "text":
            self.widget = ctk.CTkTextbox(self, height=80, corner_radius=Theme.BUTTON_RADIUS, font=Theme.FONT_BODY)
        else:
            self.widget = ctk.CTkEntry(self, height=38, corner_radius=Theme.BUTTON_RADIUS, font=Theme.FONT_BODY)
        self.widget.grid(row=1, column=0, sticky="ew")

    def get(self) -> str:
        if isinstance(self.widget, ctk.CTkTextbox):
            return self.widget.get("1.0", "end-1c").strip()
        return self.widget.get().strip()

    def set(self, value: str) -> None:
        if isinstance(self.widget, ctk.CTkTextbox):
            self.widget.delete("1.0", "end")
            self.widget.insert("1.0", value or "")
        elif isinstance(self.widget, ctk.CTkComboBox):
            self.widget.set(value or "")
        else:
            self.widget.delete(0, "end")
            self.widget.insert(0, value or "")

    def set_values(self, values: list) -> None:
        if isinstance(self.widget, ctk.CTkComboBox):
            self.widget.configure(values=values or [])


class SearchPickerDialog(ctk.CTkToplevel):
    """Modal list picker with search bar and paginated scrollable results."""

    _PER_PAGE = 50
    _DEBOUNCE_MS = 250

    def __init__(
        self,
        parent,
        title: str,
        label_fn: Callable,
        on_select: Callable,
        columns: tuple[str, ...] = ("Item",),
        row_fn: Callable | None = None,
        items: list | None = None,
        search_fn: Callable | None = None,
        allow_none: bool = True,
        none_label: str = "-- None --",
        filter_options: list[str] | None = None,
        per_page: int = 50,
    ):
        super().__init__(parent)
        self.title(title)
        self.geometry("780x520")
        self.minsize(640, 420)
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        self.configure(fg_color=Theme.PAGE_BG)

        self._items = items or []
        self._search_fn = search_fn
        self._label_fn = label_fn
        self._row_fn = row_fn or (lambda item: (label_fn(item),))
        self._on_select = on_select
        self._columns = columns
        self._allow_none = allow_none
        self._none_label = none_label
        self._per_page = per_page
        self._page = 1
        self._total = 0
        self._filtered: list = []
        self._debounce_id = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        hdr = ctk.CTkFrame(self, fg_color=Theme.ACCENT, corner_radius=0, height=52)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)
        ctk.CTkLabel(hdr, text=title, font=Theme.FONT_HEADING,
                     text_color="white", anchor="w").pack(anchor="w", padx=20, pady=14)

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=1, column=0, sticky="ew", padx=16, pady=(12, 4))
        toolbar.grid_columnconfigure(0, weight=1)

        self._search = ctk.CTkEntry(
            toolbar, placeholder_text="Search by code or description…",
            height=38, font=Theme.FONT_BODY, corner_radius=Theme.BUTTON_RADIUS,
            border_color=Theme.BORDER,
        )
        self._search.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self._search.bind("<KeyRelease>", self._schedule_refresh)

        self._filter = None
        if filter_options:
            self._filter = ctk.CTkComboBox(
                toolbar, values=filter_options, width=140, height=38,
                font=Theme.FONT_BODY, corner_radius=Theme.BUTTON_RADIUS,
                state="readonly",
            )
            self._filter.set(filter_options[0])
            self._filter.grid(row=0, column=1, padx=(0, 8))
            self._filter.configure(command=lambda _: self._reset_and_refresh())

        self._count_lbl = ctk.CTkLabel(
            self, text="", font=Theme.FONT_TINY,
            text_color=Theme.TEXT_MUTED, anchor="w",
        )
        self._count_lbl.grid(row=2, column=0, sticky="w", padx=20, pady=(0, 4))

        self._table = DataTable(self, list(columns))
        self._table.grid(row=3, column=0, sticky="nsew", padx=16, pady=(0, 4))

        self._pager = ctk.CTkFrame(self, fg_color="transparent")
        self._pager.grid(row=4, column=0, sticky="ew", padx=16, pady=(0, 8))
        self._page_lbl = ctk.CTkLabel(
            self._pager, text="", font=Theme.FONT_SMALL, text_color=Theme.TEXT_SECONDARY,
        )
        self._page_lbl.pack(side="left")
        self._prev_btn = ctk.CTkButton(
            self._pager, text="◀ Prev", width=80, height=32,
            font=Theme.FONT_SMALL, fg_color=Theme.SECONDARY,
            hover_color=Theme.BORDER, text_color=Theme.TEXT_PRIMARY,
            command=self._prev_page,
        )
        self._prev_btn.pack(side="right", padx=(4, 0))
        self._next_btn = ctk.CTkButton(
            self._pager, text="Next ▶", width=80, height=32,
            font=Theme.FONT_SMALL, fg_color=Theme.SECONDARY,
            hover_color=Theme.BORDER, text_color=Theme.TEXT_PRIMARY,
            command=self._next_page,
        )
        self._next_btn.pack(side="right")

        footer = ctk.CTkFrame(self, fg_color=Theme.PRIMARY, corner_radius=0, height=56)
        footer.grid(row=5, column=0, sticky="ew")
        footer.grid_propagate(False)

        if allow_none:
            ActionButton(footer, text=none_label, style="secondary",
                         command=self._select_none).pack(side="left", padx=16, pady=10)
        btn_fr = ctk.CTkFrame(footer, fg_color="transparent")
        btn_fr.pack(side="right", padx=16, pady=10)
        ActionButton(btn_fr, text="Select", style="success",
                     command=self._confirm).pack(side="left", padx=(0, 8))
        ActionButton(btn_fr, text="Cancel", style="secondary",
                     command=self.destroy).pack(side="left")

        self.after(50, self._refresh_list)
        self._search.focus_set()

    def _filter_value(self) -> str:
        return self._filter.get() if self._filter else "All"

    def _schedule_refresh(self, _event=None) -> None:
        self._page = 1
        if self._debounce_id:
            self.after_cancel(self._debounce_id)
        self._debounce_id = self.after(self._DEBOUNCE_MS, self._refresh_list)

    def _reset_and_refresh(self) -> None:
        self._page = 1
        self._refresh_list()

    def _prev_page(self) -> None:
        if self._page > 1:
            self._page -= 1
            self._refresh_list()

    def _next_page(self) -> None:
        max_page = max(1, (self._total + self._per_page - 1) // self._per_page)
        if self._page < max_page:
            self._page += 1
            self._refresh_list()

    def _fetch(self) -> None:
        query = self._search.get().strip()
        filter_val = self._filter_value()

        if self._search_fn:
            self._filtered, self._total = self._search_fn(
                query, filter_val, self._page, self._per_page
            )
            return

        query_lower = query.lower()
        matched = [
            item for item in self._items
            if self._passes_filter(item, filter_val) and self._matches(item, query_lower)
        ]
        self._total = len(matched)
        start = (self._page - 1) * self._per_page
        self._filtered = matched[start:start + self._per_page]

    def _update_count(self) -> None:
        if self._total == 0:
            hint = "Type a code or description to search" if self._search_fn else "No matches"
            self._count_lbl.configure(text=hint)
            return
        start = (self._page - 1) * self._per_page + 1
        end = min(self._page * self._per_page, self._total)
        self._count_lbl.configure(
            text=f"Showing {start}–{end} of {self._total} — double-click a row to select"
        )

    def _update_pager(self) -> None:
        max_page = max(1, (self._total + self._per_page - 1) // self._per_page)
        self._page_lbl.configure(text=f"Page {self._page} of {max_page}")
        self._prev_btn.configure(state="normal" if self._page > 1 else "disabled")
        self._next_btn.configure(state="normal" if self._page < max_page else "disabled")

    def _matches(self, item, query: str) -> bool:
        if not query:
            return True
        hay = " ".join(str(v) for v in self._row_fn(item)).lower()
        hay += " " + self._label_fn(item).lower()
        return query in hay

    def _passes_filter(self, item, filter_val: str) -> bool:
        if not filter_val or filter_val == "All":
            return True
        return getattr(item, "case_type", "") == filter_val

    def _refresh_list(self) -> None:
        self._debounce_id = None
        self._fetch()
        self._table.clear_rows()
        for item in self._filtered:
            self._table.add_row(
                list(self._row_fn(item)),
                on_click=lambda i=item: self._pick(i),
            )
        self._update_count()
        self._update_pager()

    def _pick(self, item) -> None:
        self._on_select(item)
        self.destroy()

    def _select_none(self) -> None:
        self._on_select(None)
        self.destroy()

    def _confirm(self) -> None:
        row = self._table.get_selected_row()
        if not row:
            return
        idx = self._table._selected_index
        if idx is not None and idx < len(self._filtered):
            self._pick(self._filtered[idx])


class SearchPickerField(ctk.CTkFrame):
    """Read-only field with a button that opens a searchable picker modal."""

    def __init__(
        self,
        master,
        label: str,
        label_fn: Callable,
        dialog_title: str = "Select Item",
        columns: tuple[str, ...] = ("Item",),
        row_fn: Callable | None = None,
        items: list | None = None,
        search_fn: Callable | None = None,
        allow_none: bool = True,
        none_label: str = "-- None --",
        filter_options: list[str] | None = None,
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self._items = items or []
        self._search_fn = search_fn
        self._label_fn = label_fn
        self._row_fn = row_fn
        self._dialog_title = dialog_title
        self._columns = columns
        self._allow_none = allow_none
        self._none_label = none_label
        self._filter_options = filter_options
        self._selected_item = None
        self._selected_label = none_label if allow_none else ""

        ctk.CTkLabel(self, text=label, font=Theme.FONT_BODY,
                     text_color=Theme.TEXT_SECONDARY, anchor="w").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.grid(row=1, column=0, columnspan=2, sticky="ew")
        row.grid_columnconfigure(0, weight=1)

        self._display = ctk.CTkEntry(
            row, height=38, font=Theme.FONT_BODY,
            corner_radius=Theme.BUTTON_RADIUS, border_color=Theme.BORDER,
            state="readonly",
        )
        self._display.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self._set_display(self._selected_label)

        ctk.CTkButton(
            row, text="Browse…", width=100, height=38,
            font=Theme.FONT_BUTTON, corner_radius=Theme.BUTTON_RADIUS,
            fg_color=Theme.ACCENT, hover_color=Theme.ACCENT_HOVER,
            command=self._open_picker,
        ).grid(row=0, column=1)

    def _set_display(self, text: str) -> None:
        self._display.configure(state="normal")
        self._display.delete(0, "end")
        self._display.insert(0, text)
        self._display.configure(state="readonly")

    def _open_picker(self) -> None:
        root = self.winfo_toplevel()
        SearchPickerDialog(
            root,
            title=self._dialog_title,
            label_fn=self._label_fn,
            on_select=self._on_picked,
            columns=self._columns,
            row_fn=self._row_fn,
            items=self._items,
            search_fn=self._search_fn,
            allow_none=self._allow_none,
            none_label=self._none_label,
            filter_options=self._filter_options,
        )

    def _on_picked(self, item) -> None:
        self._selected_item = item
        if item is None:
            self._selected_label = self._none_label
        else:
            self._selected_label = self._label_fn(item)
        self._set_display(self._selected_label)

    def update_items(self, items: list) -> None:
        self._items = items

    def get(self) -> str:
        return self._selected_label if self._selected_label != self._none_label else self._none_label

    def set(self, value: str) -> None:
        if not value or value == self._none_label:
            self._selected_item = None
            self._selected_label = self._none_label
            self._set_display(self._none_label)
            return
        self._selected_label = value
        self._selected_item = next(
            (i for i in self._items if self._label_fn(i) == value), None
        )
        self._set_display(value)

    def get_item(self):
        return self._selected_item


class ActionButton(ctk.CTkButton):
    def __init__(self, master, text: str, style: str = "primary", **kwargs):
        colors = {
            "primary": (Theme.ACCENT, Theme.ACCENT_HOVER),
            "success": (Theme.SUCCESS, "#059669"),
            "danger": (Theme.DANGER, "#DC2626"),
            "secondary": (Theme.SECONDARY, Theme.BORDER),
        }
        fg, hover = colors.get(style, colors["primary"])
        text_color = Theme.TEXT_PRIMARY if style == "secondary" else "white"
        height = kwargs.pop("height", 42)
        super().__init__(
            master, text=text, height=height, corner_radius=Theme.BUTTON_RADIUS,
            font=Theme.FONT_BUTTON, fg_color=fg, hover_color=hover,
            text_color=text_color, **kwargs
        )


class MessageDialog(ctk.CTkToplevel):
    def __init__(self, parent, title: str, message: str, msg_type: str = "info"):
        super().__init__(parent)
        self.title(title)
        self.geometry("420x200")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        colors = {"info": Theme.ACCENT, "success": Theme.SUCCESS, "error": Theme.DANGER, "warning": Theme.WARNING}
        ctk.CTkLabel(
            self, text=message, font=Theme.FONT_BODY, text_color=Theme.TEXT_PRIMARY,
            wraplength=380, justify="left",
        ).pack(padx=24, pady=(32, 16), expand=True)

        ctk.CTkButton(
            self, text="OK", width=100, fg_color=colors.get(msg_type, Theme.ACCENT),
            command=self.destroy,
        ).pack(pady=(0, 20))


def show_message(parent, title: str, message: str, msg_type: str = "info") -> None:
    MessageDialog(parent, title, message, msg_type)
