"""Price List — browse and edit PhilHealth Medical & Surgical case rates."""

from decimal import Decimal, InvalidOperation
from typing import Optional

import customtkinter as ctk

from services.philhealth_service import PhilHealthService
from utils.helpers import format_price_as_of
from views.components.theme import Theme
from views.components.widgets import ActionButton, show_message


PER_PAGE = 50


# ─────────────────────────────────────────────────────────────────────────────
#  Edit / Add dialog
# ─────────────────────────────────────────────────────────────────────────────

class _RateDialog(ctk.CTkToplevel):
    """Modal form for creating or editing a case-rate entry."""

    def __init__(self, parent, on_save, record=None):
        super().__init__(parent)
        self.on_save = on_save
        self.record  = record

        editing = record is not None
        self.title("Edit Case Rate" if editing else "Add Case Rate")
        self.geometry("520x480")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.configure(fg_color=Theme.PAGE_BG)

        # ── header ──
        hdr = ctk.CTkFrame(self, fg_color=Theme.ACCENT, corner_radius=0, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(
            hdr,
            text="Edit Case Rate" if editing else "Add Case Rate",
            font=Theme.FONT_SUBHEADING, text_color="white",
        ).pack(side="left", padx=20, pady=14)

        body = ctk.CTkFrame(self, fg_color="white", corner_radius=12,
                            border_width=1, border_color=Theme.BORDER)
        body.pack(fill="both", expand=True, padx=20, pady=16)
        body.grid_columnconfigure((0, 1), weight=1)

        def field(row, col, label, width=1):
            ctk.CTkLabel(body, text=label, font=Theme.FONT_SMALL,
                         text_color=Theme.TEXT_SECONDARY, anchor="w"
                         ).grid(row=row*2, column=col, columnspan=width,
                                sticky="w", padx=14, pady=(12, 2))
            e = ctk.CTkEntry(body, height=36, font=Theme.FONT_BODY,
                             corner_radius=8, border_color=Theme.BORDER)
            e.grid(row=row*2+1, column=col, columnspan=width,
                   sticky="ew", padx=14)
            return e

        self.code_e  = field(0, 0, "Case Code")
        self.desc_e  = field(0, 1, "Description")

        # type dropdown
        ctk.CTkLabel(body, text="Type", font=Theme.FONT_SMALL,
                     text_color=Theme.TEXT_SECONDARY, anchor="w"
                     ).grid(row=2, column=0, sticky="w", padx=14, pady=(12, 2))
        self.type_cb = ctk.CTkComboBox(
            body, values=["Medical", "Surgical"], height=36,
            font=Theme.FONT_BODY, corner_radius=8,
            border_color=Theme.BORDER, state="readonly",
        )
        self.type_cb.grid(row=3, column=0, sticky="ew", padx=14)

        # active toggle
        self.active_var = ctk.BooleanVar(value=True)
        ctk.CTkLabel(body, text="Status", font=Theme.FONT_SMALL,
                     text_color=Theme.TEXT_SECONDARY, anchor="w"
                     ).grid(row=2, column=1, sticky="w", padx=14, pady=(12, 2))
        ctk.CTkSwitch(body, text="Active", variable=self.active_var,
                      font=Theme.FONT_BODY,
                      progress_color=Theme.SUCCESS
                      ).grid(row=3, column=1, sticky="w", padx=14)

        self.rate_e = field(2, 0, "Case Rate (₱)")
        self.hff_e  = field(2, 1, "Health Facility Fee (₱)")
        self.pfe_e  = field(3, 0, "Professional Fee (₱)")

        ctk.CTkLabel(
            body,
            text="Price changes take effect today. Existing patient bills keep their original rates.",
            font=Theme.FONT_TINY, text_color=Theme.TEXT_MUTED, anchor="w", wraplength=460,
        ).grid(row=8, column=0, columnspan=2, sticky="w", padx=14, pady=(4, 0))

        if editing and record.price_effective_date:
            ctk.CTkLabel(
                body,
                text=f"Current price as of: {format_price_as_of(record.price_effective_date)}",
                font=Theme.FONT_SMALL, text_color=Theme.ACCENT, anchor="w",
            ).grid(row=9, column=0, columnspan=2, sticky="w", padx=14, pady=(2, 0))

        # ── pre-fill ──
        if editing:
            self.code_e.insert(0, record.case_code or "")
            self.code_e.configure(state="disabled", fg_color=Theme.PAGE_BG)
            self.desc_e.insert(0, record.case_description or "")
            self.type_cb.set(record.case_type or "Medical")
            self.active_var.set(bool(record.is_active))
            self.rate_e.insert(0, str(record.case_rate or 0))
            self.hff_e.insert(0,  str(record.health_facility_fee or 0))
            self.pfe_e.insert(0,  str(record.professional_fee_amount or 0))

        # ── buttons ──
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 16))
        ActionButton(btn_row, text="Cancel", style="secondary",
                     command=self.destroy).pack(side="right", padx=(8, 0))
        ActionButton(btn_row, text="Save", style="primary",
                     command=self._save).pack(side="right")

    def _dec(self, entry: ctk.CTkEntry) -> Optional[Decimal]:
        try:
            return Decimal(entry.get().strip() or "0")
        except InvalidOperation:
            return None

    def _save(self):
        code = self.code_e.get().strip()
        desc = self.desc_e.get().strip()
        if not code or not desc:
            show_message(self, "Validation", "Code and description are required.", "warning")
            return
        rate = self._dec(self.rate_e)
        hff  = self._dec(self.hff_e)
        pfe  = self._dec(self.pfe_e)
        if None in (rate, hff, pfe):
            show_message(self, "Validation", "Amounts must be valid numbers.", "warning")
            return
        self.on_save({
            "case_code":             code,
            "case_description":      desc,
            "case_type":             self.type_cb.get(),
            "case_rate":             rate,
            "health_facility_fee":   hff,
            "professional_fee_amount": pfe,
            "is_active":             self.active_var.get(),
        })
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
#  Main view
# ─────────────────────────────────────────────────────────────────────────────

class PriceListView(ctk.CTkFrame):
    def __init__(self, master, philhealth_service: PhilHealthService, **kwargs):
        super().__init__(master, fg_color=Theme.PAGE_BG, **kwargs)
        self.svc           = philhealth_service
        self._page         = 1
        self._total        = 0
        self._type_filter  = "All"
        self._query        = ""
        self._selected_id: Optional[int] = None
        self._row_data: list = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_topbar()
        self._build_toolbar()
        self._build_table()
        self._build_pagination()

    # ── top stats bar ────────────────────────────────────────────────────────
    def _build_topbar(self):
        bar = ctk.CTkFrame(self, fg_color="white", corner_radius=12,
                           border_width=1, border_color=Theme.BORDER)
        bar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        bar.grid_columnconfigure((0, 1, 2, 3), weight=1)

        def stat(col, label, color, var_name):
            card = ctk.CTkFrame(bar, fg_color="transparent")
            card.grid(row=0, column=col, padx=20, pady=14, sticky="w")
            lbl = ctk.CTkLabel(card, text="—", font=("Segoe UI", 22, "bold"),
                               text_color=color)
            lbl.pack(anchor="w")
            ctk.CTkLabel(card, text=label, font=Theme.FONT_SMALL,
                         text_color=Theme.TEXT_MUTED).pack(anchor="w")
            setattr(self, var_name, lbl)

        stat(0, "Total Medical (ICD)", Theme.ACCENT,   "_lbl_med")
        stat(1, "Total Surgical (RVS)", Theme.SUCCESS, "_lbl_surg")
        stat(2, "Showing (this page)",  Theme.PURPLE,  "_lbl_page")
        stat(3, "Total Records",        Theme.WARNING, "_lbl_total")

        # vertical dividers
        for c in (1, 2, 3):
            ctk.CTkFrame(bar, fg_color=Theme.BORDER, width=1
                         ).grid(row=0, column=c, sticky="ns", pady=8)

    # ── toolbar ──────────────────────────────────────────────────────────────
    def _build_toolbar(self):
        tb = ctk.CTkFrame(self, fg_color="transparent")
        tb.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        tb.grid_columnconfigure(1, weight=1)

        # type tabs
        tab_frame = ctk.CTkFrame(tb, fg_color="white", corner_radius=10,
                                 border_width=1, border_color=Theme.BORDER)
        tab_frame.grid(row=0, column=0, sticky="w")

        self._tab_btns = {}
        for i, label in enumerate(("All", "Medical", "Surgical")):
            btn = ctk.CTkButton(
                tab_frame, text=label, width=90, height=36,
                font=Theme.FONT_SMALL,
                fg_color=Theme.ACCENT if i == 0 else "transparent",
                text_color="white" if i == 0 else Theme.TEXT_SECONDARY,
                hover_color=Theme.ACCENT_HOVER if i == 0 else Theme.PAGE_BG,
                corner_radius=8,
                command=lambda t=label: self._set_type(t),
            )
            btn.grid(row=0, column=i, padx=3, pady=3)
            self._tab_btns[label] = btn

        # search
        search_frame = ctk.CTkFrame(tb, fg_color="white", corner_radius=10,
                                    border_width=1, border_color=Theme.BORDER)
        search_frame.grid(row=0, column=1, sticky="ew", padx=10)
        search_frame.grid_columnconfigure(0, weight=1)
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._on_search_change())
        ctk.CTkEntry(
            search_frame,
            textvariable=self._search_var,
            placeholder_text="  Search code or description...",
            height=42, font=Theme.FONT_BODY,
            border_width=0, fg_color="transparent",
        ).grid(row=0, column=0, sticky="ew", padx=8)
        ctk.CTkButton(
            search_frame, text="Search", width=90, height=36,
            font=Theme.FONT_BUTTON,
            fg_color=Theme.ACCENT, hover_color=Theme.ACCENT_HOVER,
            corner_radius=8,
            command=self._do_search,
        ).grid(row=0, column=1, padx=(0, 4), pady=3)

        # action buttons
        action_frame = ctk.CTkFrame(tb, fg_color="transparent")
        action_frame.grid(row=0, column=2, sticky="e")
        ActionButton(action_frame, text="+ Add", style="primary",
                     command=self._open_add).pack(side="left", padx=(0, 6))
        ActionButton(action_frame, text="Edit", style="secondary",
                     command=self._open_edit).pack(side="left", padx=(0, 6))
        ActionButton(action_frame, text="Delete", style="danger",
                     command=self._delete).pack(side="left")

    # ── table ─────────────────────────────────────────────────────────────────
    def _build_table(self):
        COLS = ["Code", "Type", "Description", "Case Rate (₱)",
                "Hospital Fee (₱)", "Prof. Fee (₱)", "As of", "Status"]
        WIDTHS = [80, 72, 0, 100, 110, 90, 80, 60]   # 0 = expand

        wrapper = ctk.CTkFrame(self, fg_color="white", corner_radius=12,
                               border_width=1, border_color=Theme.BORDER)
        wrapper.grid(row=2, column=0, sticky="nsew")
        wrapper.grid_columnconfigure(0, weight=1)
        wrapper.grid_rowconfigure(1, weight=1)

        # header
        hdr = ctk.CTkFrame(wrapper, fg_color=Theme.SECONDARY, corner_radius=0, height=42)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)
        self._col_weights(hdr, COLS, WIDTHS)
        for i, col in enumerate(COLS):
            ctk.CTkLabel(
                hdr, text=col, font=Theme.FONT_SUBHEADING,
                text_color=Theme.TEXT_PRIMARY, anchor="w",
            ).grid(row=0, column=i, sticky="ew", padx=10, pady=10)

        # scrollable body
        self._body = ctk.CTkScrollableFrame(wrapper, fg_color="transparent",
                                            corner_radius=0)
        self._body.grid(row=1, column=0, sticky="nsew")
        self._col_weights(self._body, COLS, WIDTHS)
        self._COLS   = COLS
        self._WIDTHS = WIDTHS

    @staticmethod
    def _col_weights(frame, cols, widths):
        for i, w in enumerate(widths):
            if w == 0:
                frame.grid_columnconfigure(i, weight=1)
            else:
                frame.grid_columnconfigure(i, minsize=w, weight=0)

    def _build_pagination(self):
        pg = ctk.CTkFrame(self, fg_color="transparent")
        pg.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        pg.grid_columnconfigure(1, weight=1)

        self._btn_prev = ActionButton(pg, text="◀  Prev", style="secondary",
                                      command=self._prev_page)
        self._btn_prev.grid(row=0, column=0)

        self._lbl_pager = ctk.CTkLabel(pg, text="", font=Theme.FONT_SMALL,
                                       text_color=Theme.TEXT_MUTED)
        self._lbl_pager.grid(row=0, column=1)

        self._btn_next = ActionButton(pg, text="Next  ▶", style="secondary",
                                      command=self._next_page)
        self._btn_next.grid(row=0, column=2)

    # ── data loading ──────────────────────────────────────────────────────────
    def _load(self):
        records, total = self.svc.search_rates(
            query=self._query,
            case_type=self._type_filter,
            page=self._page,
            per_page=PER_PAGE,
        )
        self._total   = total
        self._row_data = records
        self._selected_id = None
        self._render_rows(records)
        self._update_pagination(len(records))
        self._update_stats()

    def _update_stats(self):
        counts = self.svc.get_type_counts()
        self._lbl_med.configure(text=f"{counts.get('Medical', 0):,}")
        self._lbl_surg.configure(text=f"{counts.get('Surgical', 0):,}")
        self._lbl_page.configure(text=str(len(self._row_data)))
        self._lbl_total.configure(text=f"{self._total:,}")

    def _render_rows(self, records):
        for w in self._body.winfo_children():
            w.destroy()

        if not records:
            ctk.CTkLabel(
                self._body, text="No records found.",
                font=Theme.FONT_BODY, text_color=Theme.TEXT_MUTED,
            ).grid(row=0, column=0, columnspan=len(self._COLS), pady=40)
            return

        type_colors = {"Medical": Theme.ACCENT, "Surgical": Theme.SUCCESS}

        for idx, rec in enumerate(records):
            bg = Theme.ACCENT_LIGHT if idx % 2 == 0 else "white"
            row = ctk.CTkFrame(self._body, fg_color=bg, corner_radius=0, height=38)
            row.grid(row=idx, column=0, columnspan=len(self._COLS), sticky="ew", pady=1)
            row.grid_propagate(False)
            self._col_weights(row, self._COLS, self._WIDTHS)

            values = [
                rec.case_code,
                rec.case_type,
                rec.case_description,
                f"₱{rec.case_rate:,.2f}",
                f"₱{rec.health_facility_fee:,.2f}",
                f"₱{rec.professional_fee_amount:,.2f}",
                format_price_as_of(rec.price_effective_date),
                "Active" if rec.is_active else "Inactive",
            ]
            for col_i, val in enumerate(values):
                color = Theme.TEXT_PRIMARY
                if col_i == 1:
                    color = type_colors.get(val, Theme.TEXT_PRIMARY)
                elif col_i == 7:
                    color = Theme.SUCCESS if val == "Active" else Theme.DANGER
                elif col_i in (3, 4, 5):
                    color = Theme.PURPLE
                elif col_i == 6:
                    color = Theme.TEXT_MUTED

                lbl = ctk.CTkLabel(
                    row, text=str(val), font=Theme.FONT_BODY,
                    text_color=color, anchor="w",
                )
                lbl.grid(row=0, column=col_i, sticky="ew", padx=10, pady=6)
                lbl.configure(cursor="hand2")
                lbl.bind("<Button-1>", lambda e, r=rec, i=idx: self._select(r, i))

            row.bind("<Button-1>", lambda e, r=rec, i=idx: self._select(r, i))
            row.bind("<Double-Button-1>", lambda e, r=rec: self._open_edit_record(r))

    def _select(self, rec, idx):
        self._selected_id = rec.id
        for i, child in enumerate(self._body.winfo_children()):
            if isinstance(child, ctk.CTkFrame):
                sel = i == idx
                bg = Theme.SECONDARY if sel else (Theme.ACCENT_LIGHT if i % 2 == 0 else "white")
                child.configure(fg_color=bg)

    def _update_pagination(self, count):
        total_pages = max(1, (self._total + PER_PAGE - 1) // PER_PAGE)
        start = (self._page - 1) * PER_PAGE + 1
        end   = start + count - 1
        self._lbl_pager.configure(
            text=f"Page {self._page} of {total_pages}   ·   Showing {start}–{end} of {self._total:,} records"
        )
        self._btn_prev.configure(state="normal" if self._page > 1 else "disabled")
        self._btn_next.configure(state="normal" if self._page < total_pages else "disabled")

    # ── search / filter ───────────────────────────────────────────────────────
    def _on_search_change(self):
        # live search after 400 ms idle
        if hasattr(self, "_search_after"):
            self.after_cancel(self._search_after)
        self._search_after = self.after(400, self._do_search)

    def _do_search(self):
        self._query = self._search_var.get()
        self._page  = 1
        self._load()

    def _set_type(self, t: str):
        self._type_filter = t
        self._page = 1
        for label, btn in self._tab_btns.items():
            active = label == t
            btn.configure(
                fg_color=Theme.ACCENT if active else "transparent",
                text_color="white" if active else Theme.TEXT_SECONDARY,
                hover_color=Theme.ACCENT_HOVER if active else Theme.PAGE_BG,
            )
        self._load()

    # ── pagination ────────────────────────────────────────────────────────────
    def _prev_page(self):
        if self._page > 1:
            self._page -= 1
            self._load()

    def _next_page(self):
        total_pages = max(1, (self._total + PER_PAGE - 1) // PER_PAGE)
        if self._page < total_pages:
            self._page += 1
            self._load()

    # ── CRUD actions ─────────────────────────────────────────────────────────
    def _open_add(self):
        def save(data):
            ok, msg = self.svc.create_case_rate(data)
            if ok:
                self.svc.session.commit()
                show_message(self, "Success", msg, "success")
                self._load()
            else:
                show_message(self, "Error", msg, "error")

        _RateDialog(self, on_save=save)

    def _get_selected_record(self):
        if self._selected_id is None:
            show_message(self, "No Selection", "Click a row first.", "warning")
            return None
        return next((r for r in self._row_data if r.id == self._selected_id), None)

    def _open_edit(self):
        rec = self._get_selected_record()
        if rec:
            self._open_edit_record(rec)

    def _open_edit_record(self, rec):
        def save(data):
            ok, msg = self.svc.update_case_rate(rec.id, data)
            if ok:
                self.svc.session.commit()
                show_message(self, "Success", msg, "success")
                self._load()
            else:
                show_message(self, "Error", msg, "error")

        _RateDialog(self, on_save=save, record=rec)

    def _delete(self):
        rec = self._get_selected_record()
        if not rec:
            return
        dlg = _ConfirmDialog(
            self,
            title="Delete Rate",
            message=f"Delete [{rec.case_code}] {rec.case_description[:40]}?\nThis cannot be undone.",
            on_confirm=lambda: self._do_delete(rec.id),
        )

    def _do_delete(self, rate_id: int):
        ok, msg = self.svc.delete_case_rate(rate_id)
        if ok:
            self.svc.session.commit()
            show_message(self, "Deleted", msg, "success")
            self._load()
        else:
            show_message(self, "Error", msg, "error")

    def refresh(self):
        self._load()


# ─────────────────────────────────────────────────────────────────────────────
#  Confirm dialog
# ─────────────────────────────────────────────────────────────────────────────

class _ConfirmDialog(ctk.CTkToplevel):
    def __init__(self, parent, title: str, message: str, on_confirm):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x200")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.configure(fg_color=Theme.PAGE_BG)

        ctk.CTkLabel(
            self, text=message, font=Theme.FONT_BODY,
            text_color=Theme.TEXT_PRIMARY, wraplength=360, justify="center",
        ).pack(padx=24, pady=(28, 16), expand=True)

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=(0, 20))
        ActionButton(btn_row, text="Cancel", style="secondary",
                     command=self.destroy).pack(side="left", padx=8)
        ActionButton(btn_row, text="Delete", style="danger",
                     command=lambda: [on_confirm(), self.destroy()]).pack(side="left")
