"""Medicine inventory view — dashboard design standard."""

from datetime import date, timedelta

import customtkinter as ctk

from config.settings import EXPIRY_WARNING_DAYS
from utils.helpers import format_price_as_of
from views.components.theme import Theme
from views.components.widgets import ActionButton, FormField, PanelCard, SearchBar, show_message


def _stock_status(medicine) -> tuple[str, str, str]:
    """Return (label, color, tint) for stock badge."""
    if medicine.stock_quantity <= 0:
        return "Out of Stock", Theme.DANGER, Theme.DANGER_LIGHT
    if medicine.stock_quantity <= medicine.reorder_level:
        return "Low Stock", Theme.WARNING, Theme.WARNING_LIGHT
    return "In Stock", Theme.SUCCESS, Theme.SUCCESS_LIGHT


def _is_expiring_soon(expiration_date) -> bool:
    if not expiration_date:
        return False
    d = expiration_date.date() if hasattr(expiration_date, "date") else expiration_date
    return d <= date.today() + timedelta(days=EXPIRY_WARNING_DAYS)


# ─────────────────────────────────────────────────────────────────────────────
class _StatChip(ctk.CTkFrame):
    def __init__(self, master, label: str, color: str, tint: str, **kwargs):
        super().__init__(
            master, fg_color=tint, corner_radius=10,
            border_width=1, border_color=color, **kwargs,
        )
        self._val = ctk.CTkLabel(
            self, text="—", font=("Segoe UI", 20, "bold"), text_color=color,
        )
        self._val.pack(padx=14, pady=(10, 0), anchor="w")
        ctk.CTkLabel(
            self, text=label, font=Theme.FONT_TINY, text_color=Theme.TEXT_MUTED,
        ).pack(padx=14, pady=(0, 10), anchor="w")

    def set_value(self, v: str) -> None:
        self._val.configure(text=v)


# ─────────────────────────────────────────────────────────────────────────────
class _ContextCard(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(
            master, fg_color=Theme.CARD_BG,
            corner_radius=Theme.CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER, **kwargs,
        )
        self._bar = ctk.CTkFrame(self, fg_color=Theme.ACCENT, width=4, corner_radius=0)
        self._bar.pack(side="left", fill="y")
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(side="left", fill="both", expand=True, padx=16, pady=12)

        self._title = ctk.CTkLabel(
            body, text="No medicine selected",
            font=Theme.FONT_SUBHEADING, text_color=Theme.TEXT_PRIMARY, anchor="w",
        )
        self._title.pack(anchor="w")
        self._sub = ctk.CTkLabel(
            body, text="Select from the list or add a new medicine",
            font=Theme.FONT_TINY, text_color=Theme.TEXT_MUTED, anchor="w",
        )
        self._sub.pack(anchor="w")

        self._badge_row = ctk.CTkFrame(body, fg_color="transparent")
        self._badge_row.pack(fill="x", pady=(8, 0))

    def update(self, medicine) -> None:
        for w in self._badge_row.winfo_children():
            w.destroy()

        if medicine is None:
            self._bar.configure(fg_color=Theme.ACCENT)
            self._title.configure(text="No medicine selected")
            self._sub.configure(text="Select from the list or add a new medicine")
            return

        label, color, tint = _stock_status(medicine)
        self._bar.configure(fg_color=color)
        name = medicine.display_name
        self._title.configure(text=name)
        price = f"₱{float(medicine.selling_price):,.2f}"
        expiry = str(medicine.expiration_date or "No expiry")
        self._sub.configure(
            text=f"Stock: {medicine.stock_quantity} units  ·  Price: {price}  ·  Exp: {expiry}"
        )

        def _badge(text, c, t):
            b = ctk.CTkFrame(self._badge_row, fg_color=t, corner_radius=6)
            b.pack(side="left", padx=(0, 6))
            ctk.CTkLabel(b, text=text, font=Theme.FONT_TINY, text_color=c).pack(padx=8, pady=3)

        _badge(label, color, tint)
        if _is_expiring_soon(medicine.expiration_date):
            _badge("Expiring Soon", Theme.WARNING, Theme.WARNING_LIGHT)
        if medicine.batch_number:
            _badge(f"Batch: {medicine.batch_number}", "#0891B2", "#ECFEFF")


# ─────────────────────────────────────────────────────────────────────────────
class _MedicineRow(ctk.CTkFrame):
    def __init__(self, master, medicine, on_select, **kwargs):
        super().__init__(
            master, fg_color="transparent", corner_radius=8,
            cursor="hand2", **kwargs,
        )
        self._medicine = medicine
        self._on_select = on_select
        self._selected = False

        label, color, tint = _stock_status(medicine)

        self._bar = ctk.CTkFrame(self, fg_color="transparent", width=3, corner_radius=2)
        self._bar.pack(side="left", fill="y", padx=(4, 0))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(side="left", fill="both", expand=True, padx=(10, 12), pady=5)

        top = ctk.CTkFrame(body, fg_color="transparent")
        top.pack(fill="x")

        self._name_lbl = ctk.CTkLabel(
            top, text=medicine.display_name,
            font=("Segoe UI", 11, "bold"), text_color=Theme.TEXT_PRIMARY, anchor="w",
        )
        self._name_lbl.pack(side="left")

        badge = ctk.CTkFrame(top, fg_color=tint, corner_radius=5)
        badge.pack(side="right")
        ctk.CTkLabel(badge, text=label, font=Theme.FONT_TINY, text_color=color).pack(padx=7, pady=2)

        sub = ctk.CTkFrame(body, fg_color="transparent")
        sub.pack(fill="x")
        price = f"₱{float(medicine.selling_price):,.2f}"
        as_of = format_price_as_of(medicine.price_effective_date)
        ctk.CTkLabel(
            sub,
            text=f"Qty {medicine.stock_quantity}  ·  {price}  ·  as of {as_of}",
            font=Theme.FONT_TINY, text_color=Theme.TEXT_SECONDARY, anchor="w",
        ).pack(side="left")

        if _is_expiring_soon(medicine.expiration_date):
            ctk.CTkLabel(
                sub, text="EXP", font=("Segoe UI", 9, "bold"), text_color=Theme.WARNING,
            ).pack(side="right", padx=(4, 0))

        for w in self._walk(self):
            w.bind("<Button-1>", lambda _e: self._click())
            w.bind("<Enter>", lambda _e: self._hover(True))
            w.bind("<Leave>", lambda _e: self._hover(False))

    def _walk(self, root):
        yield root
        for c in root.winfo_children():
            yield from self._walk(c)

    def _click(self) -> None:
        self._on_select(self._medicine)

    def _hover(self, on: bool) -> None:
        if not self._selected:
            self.configure(fg_color=Theme.SECONDARY if on else "transparent")

    def select(self, active: bool) -> None:
        self._selected = active
        _, color, _ = _stock_status(self._medicine)
        self.configure(fg_color=Theme.ACCENT_LIGHT if active else "transparent")
        self._bar.configure(fg_color=color if active else "transparent")
        self._name_lbl.configure(text_color=Theme.ACCENT if active else Theme.TEXT_PRIMARY)


# ─────────────────────────────────────────────────────────────────────────────
class InventoryView(ctk.CTkFrame):
    def __init__(self, master, inventory_service, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.service = inventory_service
        self.selected_medicine = None
        self._row_widgets: list[_MedicineRow] = []

        self.grid_columnconfigure(0, weight=5)
        self.grid_columnconfigure(1, weight=7)
        self.grid_rowconfigure(0, weight=1)

        self._build_list_panel()
        self._build_detail_panel()

    # ── Left: medicine list ───────────────────────────────────────────────────
    def _build_list_panel(self) -> None:
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(2, weight=1)

        chips = ctk.CTkFrame(left, fg_color="transparent")
        chips.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        chips.grid_columnconfigure((0, 1, 2), weight=1)
        self._chip_total = _StatChip(chips, "Total Medicines", Theme.ACCENT, Theme.ACCENT_LIGHT)
        self._chip_low   = _StatChip(chips, "Low Stock",       Theme.WARNING, Theme.WARNING_LIGHT)
        self._chip_exp   = _StatChip(chips, "Expiring Soon",   Theme.DANGER,  Theme.DANGER_LIGHT)
        self._chip_total.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self._chip_low.grid(  row=0, column=1, sticky="ew", padx=4)
        self._chip_exp.grid(  row=0, column=2, sticky="ew", padx=(4, 0))

        self._search = SearchBar(left, "Search generic or brand name...", on_search=self.refresh)
        self._search.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        list_card = ctk.CTkFrame(
            left, fg_color=Theme.CARD_BG,
            corner_radius=Theme.CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER,
        )
        list_card.grid(row=2, column=0, sticky="nsew")
        list_card.grid_columnconfigure(0, weight=1)
        list_card.grid_rowconfigure(1, weight=1)

        hdr = ctk.CTkFrame(list_card, fg_color=Theme.SECONDARY, corner_radius=0, height=38)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)
        ctk.CTkLabel(
            hdr, text="Medicine Inventory",
            font=Theme.FONT_SUBHEADING, text_color=Theme.TEXT_PRIMARY, anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=14, pady=8)

        self._list_scroll = ctk.CTkScrollableFrame(list_card, fg_color="transparent")
        self._list_scroll.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)

        toolbar = ctk.CTkFrame(left, fg_color="transparent")
        toolbar.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        ActionButton(toolbar, text="+ Add Medicine", command=self._show_add_dialog).pack(
            side="left", padx=(0, 8),
        )
        ActionButton(toolbar, text="Refresh", style="secondary", command=self.refresh).pack(side="left")

    # ── Right: medicine details & stock ops ───────────────────────────────────
    def _build_detail_panel(self) -> None:
        self._detail_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._detail_scroll.grid(row=0, column=1, sticky="nsew")
        self._detail_scroll.grid_columnconfigure(0, weight=1)

        self._context = _ContextCard(self._detail_scroll)
        self._context.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        details = PanelCard(
            self._detail_scroll, "Medicine Details",
            "Pricing, stock levels, and batch information",
        )
        details.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        details.body.grid_columnconfigure((0, 1), weight=1)

        self._detail_labels: dict[str, ctk.CTkLabel] = {}
        detail_fields = [
            ("generic", "Generic Name"),
            ("brand", "Brand Name"),
            ("form", "Dosage Form"),
            ("strength", "Strength"),
            ("stock", "Current Stock"),
            ("reorder", "Reorder Level"),
            ("price", "Selling Price"),
            ("as_of", "Price As Of"),
            ("batch", "Batch Number"),
            ("expiry", "Expiration Date"),
        ]
        for i, (key, label) in enumerate(detail_fields):
            row, col = divmod(i, 2)
            px_l, px_r = (0, 6) if col == 0 else (6, 0)
            frame = ctk.CTkFrame(details.body, fg_color="transparent")
            frame.grid(row=row, column=col, sticky="ew", padx=(px_l, px_r), pady=4)
            ctk.CTkLabel(
                frame, text=label, font=Theme.FONT_TINY, text_color=Theme.TEXT_MUTED, anchor="w",
            ).pack(fill="x")
            val = ctk.CTkLabel(
                frame, text="—", font=Theme.FONT_BODY, text_color=Theme.TEXT_PRIMARY, anchor="w",
            )
            val.pack(fill="x")
            self._detail_labels[key] = val

        stock_panel = PanelCard(
            self._detail_scroll, "Stock Adjustment",
            "Record stock in or stock out for the selected medicine",
        )
        stock_panel.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        stock_panel.body.grid_columnconfigure((0, 1), weight=1)

        self._stock_qty = FormField(stock_panel.body, "Quantity")
        self._stock_qty.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        btn_row = ctk.CTkFrame(stock_panel.body, fg_color="transparent")
        btn_row.grid(row=1, column=0, columnspan=2, sticky="w")
        ActionButton(btn_row, text="Stock In", style="success", command=self._stock_in).pack(
            side="left", padx=(0, 8),
        )
        ActionButton(btn_row, text="Stock Out", style="danger", command=self._stock_out).pack(
            side="left",
        )

    # ── List refresh ──────────────────────────────────────────────────────────
    def refresh(self, query: str = "") -> None:
        q = query or self._search.get()
        medicines = self.service.search(q)

        low_stock = self.service.get_low_stock()
        expiring = self.service.get_expiring()
        low_ids = {m.id for m in low_stock}
        exp_ids = {m.id for m in expiring}

        self._chip_total.set_value(str(len(medicines)))
        self._chip_low.set_value(str(sum(1 for m in medicines if m.id in low_ids)))
        self._chip_exp.set_value(str(sum(1 for m in medicines if m.id in exp_ids)))

        for w in self._list_scroll.winfo_children():
            w.destroy()
        self._row_widgets.clear()

        if not medicines:
            ctk.CTkLabel(
                self._list_scroll, text="No medicines found.",
                font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED,
            ).pack(pady=20)
            self._select_medicine(None)
            return

        for m in medicines:
            row = _MedicineRow(self._list_scroll, m, on_select=self._select_medicine)
            row.pack(fill="x", padx=2)
            ctk.CTkFrame(self._list_scroll, fg_color=Theme.BORDER, height=1).pack(fill="x", padx=6)
            self._row_widgets.append(row)

        if self.selected_medicine:
            for rw in self._row_widgets:
                if rw._medicine.id == self.selected_medicine.id:
                    rw.select(True)
                    self._update_details(rw._medicine)
                    return
        self._select_medicine(medicines[0])

    def _select_medicine(self, medicine) -> None:
        self.selected_medicine = medicine
        for rw in self._row_widgets:
            rw.select(medicine is not None and rw._medicine.id == medicine.id)
        self._context.update(medicine)
        self._update_details(medicine)

    def _update_details(self, medicine) -> None:
        if medicine is None:
            for lbl in self._detail_labels.values():
                lbl.configure(text="—")
            return

        self._detail_labels["generic"].configure(text=medicine.generic_name or "—")
        self._detail_labels["brand"].configure(text=medicine.brand_name or "—")
        self._detail_labels["form"].configure(text=medicine.dosage_form or "—")
        self._detail_labels["strength"].configure(text=medicine.strength or "—")
        self._detail_labels["stock"].configure(text=str(medicine.stock_quantity))
        self._detail_labels["reorder"].configure(text=str(medicine.reorder_level))
        self._detail_labels["price"].configure(text=f"₱{float(medicine.selling_price):,.2f}")
        self._detail_labels["as_of"].configure(text=format_price_as_of(medicine.price_effective_date))
        self._detail_labels["batch"].configure(text=medicine.batch_number or "—")
        self._detail_labels["expiry"].configure(text=str(medicine.expiration_date or "—"))

    # ── Stock operations ──────────────────────────────────────────────────────
    def _parse_qty(self) -> int | None:
        try:
            qty = int(self._stock_qty.get())
        except ValueError:
            show_message(self, "Validation", "Enter a valid quantity.", "warning")
            return None
        return qty

    def _stock_in(self) -> None:
        if not self.selected_medicine:
            show_message(self, "Stock In", "Select a medicine from the list.", "warning")
            return
        qty = self._parse_qty()
        if qty is None:
            return
        ok, msg = self.service.stock_in(self.selected_medicine.id, qty)
        show_message(self, "Stock In", msg, "success" if ok else "error")
        if ok:
            self._stock_qty.set("")
            self.refresh()

    def _stock_out(self) -> None:
        if not self.selected_medicine:
            show_message(self, "Stock Out", "Select a medicine from the list.", "warning")
            return
        qty = self._parse_qty()
        if qty is None:
            return
        ok, msg = self.service.stock_out(self.selected_medicine.id, qty)
        show_message(self, "Stock Out", msg, "success" if ok else "error")
        if ok:
            self._stock_qty.set("")
            self.refresh()

    # ── Add medicine dialog ───────────────────────────────────────────────────
    def _show_add_dialog(self) -> None:
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add Medicine")
        w, h = 520, 560
        dialog.minsize(480, 520)
        dialog.resizable(True, True)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        dialog.configure(fg_color=Theme.PAGE_BG)
        master = self.winfo_toplevel()
        dialog.update_idletasks()
        x = master.winfo_rootx() + max(0, (master.winfo_width() - w) // 2)
        y = master.winfo_rooty() + max(0, (master.winfo_height() - h) // 2)
        dialog.geometry(f"{w}x{h}+{x}+{y}")

        card = ctk.CTkFrame(
            dialog, fg_color=Theme.CARD_BG,
            corner_radius=Theme.CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER,
        )
        card.pack(fill="both", expand=True, padx=20, pady=20)
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            card, text="Register New Medicine",
            font=Theme.FONT_SUBHEADING, text_color=Theme.TEXT_PRIMARY, anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 4))
        ctk.CTkLabel(
            card, text="Enter medicine details and initial stock",
            font=Theme.FONT_TINY, text_color=Theme.TEXT_MUTED, anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 12))

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.grid(row=2, column=0, sticky="ew", padx=16)
        body.grid_columnconfigure(0, weight=1)

        name_f = FormField(body, "Generic Name *")
        name_f.pack(fill="x", pady=4)
        brand_f = FormField(body, "Brand Name")
        brand_f.pack(fill="x", pady=4)
        price_f = FormField(body, "Selling Price")
        price_f.set("0")
        price_f.pack(fill="x", pady=4)
        stock_f = FormField(body, "Initial Stock")
        stock_f.set("0")
        stock_f.pack(fill="x", pady=4)

        def save() -> None:
            if not name_f.get():
                show_message(dialog, "Validation", "Generic name is required.", "warning")
                return
            ok, msg, _ = self.service.add_medicine({
                "generic_name": name_f.get(),
                "brand_name": brand_f.get(),
                "selling_price": float(price_f.get() or 0),
                "unit_price": float(price_f.get() or 0),
                "stock_quantity": int(stock_f.get() or 0),
            })
            show_message(dialog, "Inventory", msg, "success" if ok else "error")
            if ok:
                dialog.destroy()
                self.refresh()

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.grid(row=3, column=0, sticky="sew", padx=16, pady=(8, 20))
        ActionButton(btn_row, text="Save Medicine", command=save).pack(side="left", padx=(0, 8))
        ActionButton(btn_row, text="Cancel", style="secondary", command=dialog.destroy).pack(side="left")
