"""Medicine inventory view."""

import customtkinter as ctk

from views.components.theme import Theme
from views.components.widgets import ActionButton, DataTable, FormField, PageHeader, SearchBar, show_message


class InventoryView(ctk.CTkFrame):
    def __init__(self, master, inventory_service, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.service = inventory_service
        self.selected_id = None
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        PageHeader(self, "Medicine Inventory", "Stock management and tracking").grid(
            row=0, column=0, sticky="ew", pady=(0, 16)
        )

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        self.search = SearchBar(toolbar, "Search medicines...", on_search=self.refresh)
        self.search.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ActionButton(toolbar, text="Add Medicine", command=self._show_add_dialog).pack(side="left", padx=4)
        ActionButton(toolbar, text="Stock In", style="success", command=self._stock_in).pack(side="left", padx=4)
        ActionButton(toolbar, text="Stock Out", style="danger", command=self._stock_out).pack(side="left", padx=4)

        self.table = DataTable(
            self, ["ID", "Generic Name", "Brand", "Stock", "Price", "Expiry", "Status"]
        )
        self.table.grid(row=2, column=0, sticky="nsew")

        self.stock_qty = FormField(self, "Quantity for Stock In/Out")
        self.stock_qty.grid(row=3, column=0, sticky="w", pady=(12, 0))

    def refresh(self, query: str = "") -> None:
        medicines = self.service.search(query or self.search.get())
        self.table.clear_rows()
        for m in medicines:
            status = "Low" if m.stock_quantity <= m.reorder_level else "OK"
            self.table.add_row(
                [
                    m.id, m.generic_name, m.brand_name or "—", m.stock_quantity,
                    f"₱{m.selling_price:.2f}", str(m.expiration_date or "—"), status,
                ],
                on_click=lambda mid=m.id: setattr(self, "selected_id", mid) or None,
            )

    def _show_add_dialog(self) -> None:
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add Medicine")
        dialog.geometry("480x400")
        dialog.transient(self)
        dialog.grab_set()

        name_f = FormField(dialog, "Generic Name *")
        name_f.pack(fill="x", padx=20, pady=(20, 8))
        brand_f = FormField(dialog, "Brand Name")
        brand_f.pack(fill="x", padx=20, pady=8)
        price_f = FormField(dialog, "Selling Price")
        price_f.set("0")
        price_f.pack(fill="x", padx=20, pady=8)
        stock_f = FormField(dialog, "Initial Stock")
        stock_f.set("0")
        stock_f.pack(fill="x", padx=20, pady=8)

        def save():
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

        ActionButton(dialog, text="Save", command=save).pack(pady=20)

    def _stock_in(self) -> None:
        if not self.selected_id:
            show_message(self, "Stock In", "Select a medicine from the list.", "warning")
            return
        try:
            qty = int(self.stock_qty.get())
        except ValueError:
            show_message(self, "Validation", "Enter a valid quantity.", "warning")
            return
        ok, msg = self.service.stock_in(self.selected_id, qty)
        show_message(self, "Stock In", msg, "success" if ok else "error")
        if ok:
            self.refresh()

    def _stock_out(self) -> None:
        if not self.selected_id:
            show_message(self, "Stock Out", "Select a medicine from the list.", "warning")
            return
        try:
            qty = int(self.stock_qty.get())
        except ValueError:
            show_message(self, "Validation", "Enter a valid quantity.", "warning")
            return
        ok, msg = self.service.stock_out(self.selected_id, qty)
        show_message(self, "Stock Out", msg, "success" if ok else "error")
        if ok:
            self.refresh()
