"""Login view."""

import customtkinter as ctk

from views.components.theme import Theme


class LoginView(ctk.CTkFrame):
    def __init__(self, master, on_login, **kwargs):
        super().__init__(master, fg_color=Theme.PAGE_BG, **kwargs)
        self.on_login = on_login
        self._build_ui()

    def _build_ui(self) -> None:
        card = ctk.CTkFrame(
            self, fg_color=Theme.PRIMARY, corner_radius=Theme.CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER, width=740, height=520,
        )
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.pack_propagate(False)

        brand = ctk.CTkFrame(card, fg_color=Theme.ACCENT, corner_radius=0, width=340)
        brand.pack(side="left", fill="y")
        brand.pack_propagate(False)

        ctk.CTkLabel(brand, text="🏥", font=("Segoe UI Emoji", 56)).pack(pady=(80, 16))
        ctk.CTkLabel(brand, text="Clinic CMS", font=Theme.FONT_DISPLAY, text_color="white").pack()
        ctk.CTkLabel(
            brand,
            text="Professional clinic\nmanagement for\nmodern practices",
            font=Theme.FONT_BODY, text_color="#BFDBFE", justify="center",
        ).pack(pady=(12, 0))

        form_panel = ctk.CTkFrame(card, fg_color=Theme.PRIMARY, corner_radius=0)
        form_panel.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            form_panel, text="Welcome back", font=Theme.FONT_TITLE, text_color=Theme.TEXT_PRIMARY,
        ).pack(pady=(48, 4))
        ctk.CTkLabel(
            form_panel, text="Sign in to your account", font=Theme.FONT_BODY, text_color=Theme.TEXT_SECONDARY,
        ).pack(pady=(0, 32))

        form = ctk.CTkFrame(form_panel, fg_color="transparent")
        form.pack(fill="x", padx=40)

        ctk.CTkLabel(form, text="Username", font=Theme.FONT_SMALL, text_color=Theme.TEXT_SECONDARY, anchor="w").pack(
            fill="x", pady=(0, 4)
        )
        self.username_entry = ctk.CTkEntry(
            form, height=44, corner_radius=Theme.BUTTON_RADIUS, font=Theme.FONT_BODY, border_color=Theme.BORDER,
        )
        self.username_entry.pack(fill="x", pady=(0, 16))
        self.username_entry.insert(0, "admin")

        ctk.CTkLabel(form, text="Password", font=Theme.FONT_SMALL, text_color=Theme.TEXT_SECONDARY, anchor="w").pack(
            fill="x", pady=(0, 4)
        )
        self.password_entry = ctk.CTkEntry(
            form, height=44, corner_radius=Theme.BUTTON_RADIUS, font=Theme.FONT_BODY,
            show="•", border_color=Theme.BORDER,
        )
        self.password_entry.pack(fill="x", pady=(0, 28))
        self.password_entry.insert(0, "admin123")
        self.password_entry.bind("<Return>", lambda e: self._login())

        self.login_btn = ctk.CTkButton(
            form, text="Sign In", height=48, corner_radius=Theme.BUTTON_RADIUS,
            font=Theme.FONT_BUTTON, fg_color=Theme.ACCENT, hover_color=Theme.ACCENT_HOVER,
            command=self._login,
        )
        self.login_btn.pack(fill="x")

        ctk.CTkLabel(
            form_panel, text="Default: admin / admin123", font=Theme.FONT_TINY, text_color=Theme.TEXT_MUTED,
        ).pack(side="bottom", pady=24)

    def _login(self) -> None:
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        if not username or not password:
            return
        self.login_btn.configure(state="disabled", text="Signing in...")
        self.update_idletasks()
        if not self.on_login(username, password):
            self.login_btn.configure(state="normal", text="Sign In")
