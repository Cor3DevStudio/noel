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
    def __init__(self, master, columns: list, **kwargs):
        super().__init__(
            master, fg_color=Theme.CARD_BG, corner_radius=Theme.CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER, **kwargs
        )
        self.columns = columns
        self.rows: list = []
        self._build_header()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color=Theme.SECONDARY, corner_radius=0)
        header.pack(fill="x", padx=2, pady=(2, 0))
        for i, col in enumerate(self.columns):
            header.grid_columnconfigure(i, weight=1)
            ctk.CTkLabel(
                header, text=col, font=Theme.FONT_SUBHEADING,
                text_color=Theme.TEXT_PRIMARY, anchor="w",
            ).grid(row=0, column=i, sticky="ew", padx=12, pady=10)

    def clear_rows(self) -> None:
        for row in self.rows:
            row.destroy()
        self.rows.clear()

    def add_row(self, values: list, on_click: Optional[Callable] = None) -> None:
        row_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        row_frame.pack(fill="x", padx=2, pady=1)
        for i, val in enumerate(values):
            row_frame.grid_columnconfigure(i, weight=1)
            lbl = ctk.CTkLabel(
                row_frame, text=str(val), font=Theme.FONT_BODY,
                text_color=Theme.TEXT_PRIMARY, anchor="w",
            )
            lbl.grid(row=0, column=i, sticky="ew", padx=12, pady=8)
            if on_click:
                lbl.bind("<Button-1>", lambda e, fn=on_click: fn())
                lbl.configure(cursor="hand2")
        self.rows.append(row_frame)


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
        super().__init__(
            master, text=text, height=42, corner_radius=Theme.BUTTON_RADIUS,
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
