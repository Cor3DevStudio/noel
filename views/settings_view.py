"""Settings and administration view — dashboard design standard."""

import customtkinter as ctk
from tkinter import filedialog

from config.settings import PAGE_PERMISSIONS
from utils.helpers import format_price_as_of
from utils.security import session_manager
from views.components.theme import Theme
from views.components.widgets import ActionButton, FormField, PanelCard, show_message


_ROLE_COLOR = {
    "Administrator": (Theme.ACCENT,   Theme.ACCENT_LIGHT),
    "Doctor":        ("#0891B2",      "#ECFEFF"),
    "Receptionist":  (Theme.PURPLE,   Theme.PURPLE_LIGHT),
    "Cashier":       (Theme.WARNING,  Theme.WARNING_LIGHT),
}


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
            body, text="—", font=Theme.FONT_SUBHEADING,
            text_color=Theme.TEXT_PRIMARY, anchor="w",
        )
        self._title.pack(anchor="w")
        self._sub = ctk.CTkLabel(
            body, text="", font=Theme.FONT_TINY,
            text_color=Theme.TEXT_MUTED, anchor="w",
        )
        self._sub.pack(anchor="w")

    def update(self, title: str, sub: str, color: str = Theme.ACCENT) -> None:
        self._bar.configure(fg_color=color)
        self._title.configure(text=title)
        self._sub.configure(text=sub)


class _UserRow(ctk.CTkFrame):
    def __init__(self, master, user, on_select, **kwargs):
        super().__init__(
            master, fg_color="transparent", corner_radius=8,
            cursor="hand2", **kwargs,
        )
        self._user = user
        self._on_select = on_select
        self._selected = False

        role_name = user.role.name if user.role else "—"
        color, tint = _ROLE_COLOR.get(role_name, (Theme.ACCENT, Theme.ACCENT_LIGHT))
        if not user.is_active:
            color, tint = Theme.DANGER, Theme.DANGER_LIGHT

        self._bar = ctk.CTkFrame(self, fg_color="transparent", width=3, corner_radius=2)
        self._bar.pack(side="left", fill="y", padx=(4, 0))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(side="left", fill="both", expand=True, padx=(10, 12), pady=5)

        top = ctk.CTkFrame(body, fg_color="transparent")
        top.pack(fill="x")
        self._name_lbl = ctk.CTkLabel(
            top, text=user.full_name,
            font=("Segoe UI", 11, "bold"), text_color=Theme.TEXT_PRIMARY, anchor="w",
        )
        self._name_lbl.pack(side="left")

        badge = ctk.CTkFrame(top, fg_color=tint, corner_radius=5)
        badge.pack(side="right")
        status = "Active" if user.is_active else "Inactive"
        ctk.CTkLabel(
            badge, text=status, font=Theme.FONT_TINY, text_color=color,
        ).pack(padx=7, pady=2)

        sub = ctk.CTkFrame(body, fg_color="transparent")
        sub.pack(fill="x")
        last_login = str(user.last_login)[:16] if user.last_login else "Never"
        ctk.CTkLabel(
            sub,
            text=f"@{user.username}  ·  {role_name}  ·  Last login {last_login}",
            font=Theme.FONT_TINY, text_color=Theme.TEXT_SECONDARY, anchor="w",
        ).pack(side="left")

        for w in self._walk(self):
            w.bind("<Button-1>", lambda _e: self._click())
            w.bind("<Enter>", lambda _e: self._hover(True))
            w.bind("<Leave>", lambda _e: self._hover(False))

    def _walk(self, root):
        yield root
        for child in root.winfo_children():
            yield from self._walk(child)

    def _click(self) -> None:
        self._on_select(self._user)

    def _hover(self, on: bool) -> None:
        if not self._selected:
            self.configure(fg_color=Theme.SECONDARY if on else "transparent")

    def select(self, active: bool) -> None:
        self._selected = active
        role_name = self._user.role.name if self._user.role else "—"
        color, _ = _ROLE_COLOR.get(role_name, (Theme.ACCENT, Theme.ACCENT_LIGHT))
        if not self._user.is_active:
            color = Theme.DANGER
        self.configure(fg_color=Theme.ACCENT_LIGHT if active else "transparent")
        self._bar.configure(fg_color=color if active else "transparent")
        self._name_lbl.configure(text_color=Theme.ACCENT if active else Theme.TEXT_PRIMARY)


class _LogRow(ctk.CTkFrame):
    def __init__(self, master, log, username: str = "—", full_name: str = "System", **kwargs):
        super().__init__(
            master, fg_color=Theme.SECONDARY, corner_radius=8,
            border_width=1, border_color=Theme.BORDER, **kwargs,
        )
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="x", padx=12, pady=8)

        top = ctk.CTkFrame(body, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(
            top, text=log.action or "—",
            font=("Segoe UI", 11, "bold"), text_color=Theme.TEXT_PRIMARY, anchor="w",
        ).pack(side="left")

        badge = ctk.CTkFrame(top, fg_color=Theme.ACCENT_LIGHT, corner_radius=5)
        badge.pack(side="right", padx=(8, 0))
        ctk.CTkLabel(
            badge, text=log.module or "—",
            font=Theme.FONT_TINY, text_color=Theme.ACCENT,
        ).pack(padx=7, pady=2)
        ctk.CTkLabel(
            top, text=str(log.created_at)[:19],
            font=Theme.FONT_TINY, text_color=Theme.TEXT_MUTED, anchor="e",
        ).pack(side="right")

        ctk.CTkLabel(
            body,
            text=f"{full_name} (@{username})  ·  {(log.description or '')[:120]}",
            font=Theme.FONT_TINY, text_color=Theme.TEXT_SECONDARY, anchor="w",
        ).pack(fill="x", pady=(2, 0))


class _ConfirmDialog(ctk.CTkToplevel):
    def __init__(self, parent, title: str, message: str, on_confirm, confirm_label: str = "Confirm"):
        super().__init__(parent)
        self.title(title)
        self.geometry("420x200")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.configure(fg_color=Theme.PAGE_BG)

        ctk.CTkLabel(
            self, text=message, font=Theme.FONT_BODY,
            text_color=Theme.TEXT_PRIMARY, wraplength=380, justify="center",
        ).pack(padx=24, pady=(28, 16), expand=True)

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=(0, 20))
        ActionButton(btn_row, text="Cancel", style="secondary", command=self.destroy).pack(
            side="left", padx=8
        )
        ActionButton(
            btn_row, text=confirm_label, style="danger",
            command=lambda: [on_confirm(), self.destroy()],
        ).pack(side="left")


# ─────────────────────────────────────────────────────────────────────────────
class SettingsView(ctk.CTkFrame):
    SECTIONS = [
        ("hospital",    "Hospital Info"),
        ("users",       "Users"),
        ("permissions", "Permissions"),
        ("backup",      "Backup & Logs"),
        ("account",     "My Account"),
    ]

    def __init__(self, master, settings_service, auth_service, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.settings_service = settings_service
        self.auth_service = auth_service
        self._selected_user = None
        self._user_rows: list[_UserRow] = []
        self._section_frames: dict[str, ctk.CTkFrame] = {}
        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        self._current_section = "hospital"

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_shell()
        self._show_section("hospital")
        self._load_settings()

    # ── Shell: section nav + content ──────────────────────────────────────────
    def _build_shell(self) -> None:
        nav = ctk.CTkFrame(self, fg_color=Theme.CARD_BG, corner_radius=Theme.CORNER_RADIUS,
                           border_width=1, border_color=Theme.BORDER)
        nav.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        nav_inner = ctk.CTkFrame(nav, fg_color="transparent")
        nav_inner.pack(fill="x", padx=12, pady=10)

        for key, label in self.SECTIONS:
            if key == "permissions" and not session_manager.has_permission("users"):
                continue
            btn = ctk.CTkButton(
                nav_inner, text=label, height=36, corner_radius=8,
                font=Theme.FONT_SMALL, fg_color="transparent",
                text_color=Theme.TEXT_SECONDARY, hover_color=Theme.SECONDARY,
                command=lambda k=key: self._show_section(k),
            )
            btn.pack(side="left", padx=(0, 6))
            self._nav_buttons[key] = btn

        self._content = ctk.CTkFrame(self, fg_color="transparent")
        self._content.grid(row=1, column=0, sticky="nsew")
        self._content.grid_columnconfigure(0, weight=1)
        self._content.grid_rowconfigure(0, weight=1)

        self._build_hospital_section()
        self._build_users_section()
        if session_manager.has_permission("users"):
            self._build_permissions_section()
        self._build_backup_section()
        self._build_account_section()

    def _show_section(self, key: str) -> None:
        if key != self._current_section:
            label = dict(self.SECTIONS).get(key, key)
            self.settings_service.log_action(
                "OPEN_SECTION", "Settings", f"Opened {label} section",
            )
        self._current_section = key
        for section_key, frame in self._section_frames.items():
            if section_key == key:
                frame.grid(row=0, column=0, sticky="nsew")
            else:
                frame.grid_forget()

        for nav_key, btn in self._nav_buttons.items():
            if nav_key == key:
                btn.configure(fg_color=Theme.ACCENT, text_color="white",
                              hover_color=Theme.ACCENT_HOVER)
            else:
                btn.configure(fg_color="transparent", text_color=Theme.TEXT_SECONDARY,
                              hover_color=Theme.SECONDARY)

        if key == "users":
            self._refresh_users()
        elif key == "backup":
            self._refresh_logs()
        elif key == "permissions" and hasattr(self, "permission_user_combo"):
            self._refresh_permission_users()
        elif key == "hospital":
            self._load_settings()

    def refresh(self) -> None:
        self._show_section(self._current_section)

    # ── Hospital Info ─────────────────────────────────────────────────────────
    def _build_hospital_section(self) -> None:
        frame = ctk.CTkScrollableFrame(self._content, fg_color="transparent")
        self._section_frames["hospital"] = frame
        frame.grid_columnconfigure(0, weight=1)

        self._hospital_ctx = _ContextCard(frame)
        self._hospital_ctx.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self._hospital_ctx.update(
            "Hospital Configuration",
            "Facility details used on receipts, reports and PhilHealth forms",
        )

        facility = PanelCard(frame, "Facility Details", "Name, contact and accreditation")
        facility.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        facility.body.grid_columnconfigure((0, 1), weight=1)

        self.clinic_fields = {}
        fields = [
            ("clinic_name", "Hospital Name"), ("clinic_phone", "Phone"),
            ("clinic_email", "Email"), ("consultation_fee", "Consultation Fee"),
            ("tax_id", "Tax ID"), ("philhealth_accreditation", "PhilHealth Accreditation"),
        ]
        for i, (key, label) in enumerate(fields):
            ff = FormField(facility.body, label)
            ff.grid(row=i // 2, column=i % 2, sticky="ew", padx=(0, 6) if i % 2 == 0 else (6, 0), pady=4)
            self.clinic_fields[key] = ff

        self.address_field = FormField(facility.body, "Address", "text")
        self.address_field.grid(row=3, column=0, columnspan=2, sticky="ew", pady=4)

        receipt = PanelCard(frame, "Receipt Settings", "Header and footer text on printed receipts")
        receipt.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        receipt.body.grid_columnconfigure(0, weight=1)
        self.receipt_header = FormField(receipt.body, "Receipt Header", "text")
        self.receipt_header.pack(fill="x", pady=4)
        self.receipt_footer = FormField(receipt.body, "Receipt Footer", "text")
        self.receipt_footer.pack(fill="x", pady=4)

        self.fee_asof_lbl = ctk.CTkLabel(
            frame, text="", font=Theme.FONT_TINY, text_color=Theme.TEXT_MUTED, anchor="w",
        )
        self.fee_asof_lbl.grid(row=3, column=0, sticky="w", pady=(0, 8))

        footer = ctk.CTkFrame(frame, fg_color="transparent")
        footer.grid(row=4, column=0, sticky="ew", pady=(0, 8))
        ActionButton(footer, text="Save Changes", command=self._save_settings).pack(side="left", padx=(0, 8))
        ActionButton(footer, text="Reload", style="secondary", command=self._load_settings).pack(side="left")

    # ── Users ─────────────────────────────────────────────────────────────────
    def _build_users_section(self) -> None:
        frame = ctk.CTkFrame(self._content, fg_color="transparent")
        self._section_frames["users"] = frame
        frame.grid_columnconfigure(0, weight=5)
        frame.grid_columnconfigure(1, weight=7)
        frame.grid_rowconfigure(0, weight=1)

        # Left: list
        left = ctk.CTkFrame(frame, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(2, weight=1)

        chips = ctk.CTkFrame(left, fg_color="transparent")
        chips.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        chips.grid_columnconfigure((0, 1, 2), weight=1)
        self._chip_users_total    = _StatChip(chips, "Total Users", Theme.ACCENT,  Theme.ACCENT_LIGHT)
        self._chip_users_active   = _StatChip(chips, "Active",      Theme.SUCCESS, Theme.SUCCESS_LIGHT)
        self._chip_users_inactive = _StatChip(chips, "Inactive",    Theme.DANGER,  Theme.DANGER_LIGHT)
        self._chip_users_total.grid(   row=0, column=0, sticky="ew", padx=(0, 4))
        self._chip_users_active.grid(  row=0, column=1, sticky="ew", padx=4)
        self._chip_users_inactive.grid(row=0, column=2, sticky="ew", padx=(4, 0))

        search_row = ctk.CTkFrame(left, fg_color="transparent")
        search_row.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        search_row.grid_columnconfigure(0, weight=1)
        self._user_search = ctk.CTkEntry(
            search_row, placeholder_text="Search username or name…",
            height=38, font=Theme.FONT_BODY, corner_radius=Theme.BUTTON_RADIUS,
            border_color=Theme.BORDER,
        )
        self._user_search.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self._user_search.bind("<KeyRelease>", lambda _e: self._refresh_users())
        ActionButton(search_row, text="Search", command=self._refresh_users).grid(row=0, column=1)

        list_card = ctk.CTkFrame(
            left, fg_color=Theme.CARD_BG, corner_radius=Theme.CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER,
        )
        list_card.grid(row=2, column=0, sticky="nsew")
        list_card.grid_columnconfigure(0, weight=1)
        list_card.grid_rowconfigure(1, weight=1)

        hdr = ctk.CTkFrame(list_card, fg_color=Theme.SECONDARY, corner_radius=0, height=38)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)
        ctk.CTkLabel(
            hdr, text="User Accounts", font=Theme.FONT_SUBHEADING,
            text_color=Theme.TEXT_PRIMARY, anchor="w",
        ).pack(side="left", padx=14, pady=8)

        self._users_scroll = ctk.CTkScrollableFrame(list_card, fg_color="transparent")
        self._users_scroll.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)

        list_toolbar = ctk.CTkFrame(left, fg_color="transparent")
        list_toolbar.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        ActionButton(list_toolbar, text="+ Add User", command=self._new_user).pack(side="left", padx=(0, 8))
        ActionButton(list_toolbar, text="Refresh", style="secondary",
                     command=self._refresh_users).pack(side="left")

        # Right: detail form
        right = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)

        self._user_ctx = _ContextCard(right)
        self._user_ctx.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self._user_ctx.update("New User", "Fill in the form below or select a user from the list")

        account_panel = PanelCard(right, "Account Details", "Login credentials and role assignment")
        account_panel.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        account_panel.body.grid_columnconfigure((0, 1), weight=1)

        roles = [r.name for r in self.auth_service.get_roles()]
        self.user_fullname = FormField(account_panel.body, "Full Name")
        self.user_fullname.grid(row=0, column=0, sticky="ew", padx=(0, 6), pady=4)
        self.user_username = FormField(account_panel.body, "Username")
        self.user_username.grid(row=0, column=1, sticky="ew", padx=(6, 0), pady=4)
        self.user_email = FormField(account_panel.body, "Email")
        self.user_email.grid(row=1, column=0, sticky="ew", padx=(0, 6), pady=4)
        self.user_role = FormField(account_panel.body, "Role", "combo", roles)
        self.user_role.grid(row=1, column=1, sticky="ew", padx=(6, 0), pady=4)
        self.user_password = FormField(account_panel.body, "Password")
        self.user_password.grid(row=2, column=0, sticky="ew", padx=(0, 6), pady=4)
        self.user_password_confirm = FormField(account_panel.body, "Confirm Password")
        self.user_password_confirm.grid(row=2, column=1, sticky="ew", padx=(6, 0), pady=4)

        self._user_pw_hint = ctk.CTkLabel(
            account_panel.body,
            text="Leave password blank when editing to keep the current password.",
            font=Theme.FONT_TINY, text_color=Theme.TEXT_MUTED, anchor="w",
        )
        self._user_pw_hint.grid(row=3, column=0, columnspan=2, sticky="w", pady=(4, 0))

        actions = ctk.CTkFrame(right, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        ActionButton(actions, text="Save User", command=self._save_user).pack(side="left", padx=(0, 8))
        ActionButton(actions, text="Clear Form", style="secondary",
                     command=self._new_user).pack(side="left", padx=(0, 8))
        ActionButton(actions, text="Reset Password", style="secondary",
                     command=self._reset_user_password).pack(side="left", padx=(0, 8))
        self._toggle_btn = ActionButton(actions, text="Deactivate", style="danger",
                                        command=self._toggle_user_status)
        self._toggle_btn.pack(side="left")

    # ── Permissions ───────────────────────────────────────────────────────────
    def _build_permissions_section(self) -> None:
        frame = ctk.CTkScrollableFrame(self._content, fg_color="transparent")
        self._section_frames["permissions"] = frame
        frame.grid_columnconfigure(0, weight=1)

        ctx = _ContextCard(frame)
        ctx.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ctx.update(
            "Page Access Control",
            "Override which sidebar pages each user can see",
        )

        picker = PanelCard(frame, "Select User", "Choose a user to view or edit their page access")
        picker.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        picker.body.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            picker.body, text="User", font=Theme.FONT_BODY,
            text_color=Theme.TEXT_SECONDARY,
        ).grid(row=0, column=0, sticky="w", padx=(0, 12), pady=4)
        self.permission_user_combo = ctk.CTkComboBox(
            picker.body, values=["No users available"],
            height=38, corner_radius=Theme.BUTTON_RADIUS, font=Theme.FONT_BODY,
            command=self._load_user_permissions,
        )
        self.permission_user_combo.grid(row=0, column=1, sticky="ew", pady=4)

        self.permission_status = ctk.CTkLabel(
            frame, text="", font=Theme.FONT_TINY, text_color=Theme.TEXT_MUTED, anchor="w",
        )
        self.permission_status.grid(row=2, column=0, sticky="w", pady=(0, 8))

        access = PanelCard(frame, "Allowed Pages", "Checked pages appear in the user's sidebar menu")
        access.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        access.body.grid_columnconfigure((0, 1), weight=1)

        self.permission_vars = {}
        for index, (key, label) in enumerate(PAGE_PERMISSIONS):
            var = ctk.BooleanVar(value=False)
            self.permission_vars[key] = var
            ctk.CTkCheckBox(
                access.body, text=label, variable=var,
                font=Theme.FONT_BODY, text_color=Theme.TEXT_PRIMARY,
            ).grid(row=index // 2, column=index % 2, sticky="w", padx=8, pady=8)

        perm_actions = ctk.CTkFrame(frame, fg_color="transparent")
        perm_actions.grid(row=4, column=0, sticky="ew", pady=(0, 8))
        ActionButton(perm_actions, text="Save Permissions",
                     command=self._save_user_permissions).pack(side="left", padx=(0, 8))
        ActionButton(perm_actions, text="Reset to Role Defaults", style="secondary",
                     command=self._reset_user_permissions).pack(side="left", padx=(0, 8))
        ActionButton(perm_actions, text="Reload", style="secondary",
                     command=self._refresh_permission_users).pack(side="left")

    # ── Backup & Logs ─────────────────────────────────────────────────────────
    def _build_backup_section(self) -> None:
        frame = ctk.CTkFrame(self._content, fg_color="transparent")
        self._section_frames["backup"] = frame
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(3, weight=1)

        chips = ctk.CTkFrame(frame, fg_color="transparent")
        chips.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        chips.grid_columnconfigure((0, 1), weight=1)
        self._chip_log_count = _StatChip(chips, "Activity Logs", Theme.ACCENT, Theme.ACCENT_LIGHT)
        self._chip_backup_hint = _StatChip(chips, "Database", Theme.SUCCESS, Theme.SUCCESS_LIGHT)
        self._chip_log_count.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self._chip_backup_hint.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        self._chip_backup_hint.set_value("Ready")

        ctx = _ContextCard(frame)
        ctx.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        ctx.update("Backup & Restore", "Export or restore the MariaDB database as JSON (no mysqldump needed)")

        backup_actions = ctk.CTkFrame(frame, fg_color="transparent")
        backup_actions.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        ActionButton(backup_actions, text="Backup Database", command=self._backup).pack(
            side="left", padx=(0, 8)
        )
        ActionButton(backup_actions, text="Restore Database", style="secondary",
                     command=self._restore).pack(side="left", padx=(0, 8))
        ActionButton(backup_actions, text="Refresh Logs", style="secondary",
                     command=self._refresh_logs).pack(side="left")

        logs_panel = PanelCard(frame, "Recent Activity", "Last 50 system actions")
        logs_panel.grid(row=3, column=0, sticky="nsew")
        frame.grid_rowconfigure(3, weight=1)
        logs_panel.grid_rowconfigure(1, weight=1)

        self._logs_scroll = ctk.CTkScrollableFrame(logs_panel.body, fg_color="transparent")
        self._logs_scroll.pack(fill="both", expand=True)

    # ── My Account ────────────────────────────────────────────────────────────
    def _build_account_section(self) -> None:
        frame = ctk.CTkScrollableFrame(self._content, fg_color="transparent")
        self._section_frames["account"] = frame
        frame.grid_columnconfigure(0, weight=1)

        user = session_manager.get_current_user()
        ctx = _ContextCard(frame)
        ctx.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        if user:
            ctx.update(user["full_name"], f"@{user['username']}  ·  {user['role']}")
        else:
            ctx.update("My Account", "Update your login credentials")

        username_panel = PanelCard(frame, "Change Username", "Must be at least 3 characters")
        username_panel.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        username_panel.body.grid_columnconfigure(0, weight=1)
        self.new_username = FormField(username_panel.body, "New Username")
        self.new_username.pack(fill="x", pady=4)
        ActionButton(username_panel.body, text="Update Username",
                     command=self._change_username).pack(anchor="w", pady=(8, 0))

        password_panel = PanelCard(frame, "Change Password", "Requires your current password")
        password_panel.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        password_panel.body.grid_columnconfigure(0, weight=1)
        self.current_password = FormField(password_panel.body, "Current Password")
        self.current_password.pack(fill="x", pady=4)
        self.new_password = FormField(password_panel.body, "New Password")
        self.new_password.pack(fill="x", pady=4)
        ActionButton(password_panel.body, text="Update Password",
                     command=self._change_password).pack(anchor="w", pady=(8, 0))

    # ── Hospital actions ──────────────────────────────────────────────────────
    def _load_settings(self) -> None:
        settings = self.settings_service.get_settings()
        for key, field in self.clinic_fields.items():
            field.set(str(getattr(settings, key, "")))
        self.address_field.set(settings.clinic_address or "")
        self.receipt_header.set(settings.receipt_header or "")
        self.receipt_footer.set(settings.receipt_footer or "")
        as_of = format_price_as_of(settings.consultation_fee_effective_date)
        self.fee_asof_lbl.configure(
            text=f"Consultation fee price as of: {as_of} — changing the fee updates this date."
        )
        if hasattr(self, "_hospital_ctx"):
            self._hospital_ctx.update(
                settings.clinic_name or "Hospital",
                settings.clinic_phone or "No phone on file",
            )

    def _save_settings(self) -> None:
        data = {key: field.get() for key, field in self.clinic_fields.items()}
        data["clinic_address"] = self.address_field.get()
        data["receipt_header"] = self.receipt_header.get()
        data["receipt_footer"] = self.receipt_footer.get()
        try:
            data["consultation_fee"] = float(data.get("consultation_fee", 500))
        except ValueError:
            data["consultation_fee"] = 500
        ok, msg = self.settings_service.update_settings(data)
        show_message(self, "Settings", msg, "success" if ok else "error")
        if ok:
            self._load_settings()

    # ── User list & form ──────────────────────────────────────────────────────
    def _filter_users(self, users: list) -> list:
        query = self._user_search.get().strip().lower()
        if not query:
            return users
        return [
            u for u in users
            if query in u.username.lower()
            or query in u.full_name.lower()
            or (u.email and query in u.email.lower())
        ]

    def _refresh_users(self) -> None:
        users = self.auth_service.get_all_users_with_roles()
        filtered = self._filter_users(users)

        for w in self._users_scroll.winfo_children():
            w.destroy()
        self._user_rows.clear()

        active = sum(1 for u in users if u.is_active)
        self._chip_users_total.set_value(str(len(users)))
        self._chip_users_active.set_value(str(active))
        self._chip_users_inactive.set_value(str(len(users) - active))

        if not filtered:
            ctk.CTkLabel(
                self._users_scroll, text="No users match your search.",
                font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED,
            ).pack(pady=20)
            return

        for user in filtered:
            row = _UserRow(self._users_scroll, user, self._select_user)
            row.pack(fill="x", pady=1)
            self._user_rows.append(row)
            if self._selected_user and self._selected_user.id == user.id:
                row.select(True)

    def _select_user(self, user) -> None:
        self._selected_user = user
        for row in self._user_rows:
            row.select(row._user.id == user.id)

        role_name = user.role.name if user.role else "—"
        status = "Active" if user.is_active else "Inactive"
        color, _ = _ROLE_COLOR.get(role_name, (Theme.ACCENT, Theme.ACCENT_LIGHT))
        if not user.is_active:
            color = Theme.DANGER
        self._user_ctx.update(user.full_name, f"@{user.username}  ·  {role_name}  ·  {status}", color)

        self.user_fullname.set(user.full_name)
        self.user_username.set(user.username)
        self.user_email.set(user.email or "")
        self.user_role.set(role_name)
        self.user_password.set("")
        self.user_password_confirm.set("")

        self._toggle_btn.configure(
            text="Activate" if not user.is_active else "Deactivate",
            style="success" if not user.is_active else "danger",
        )

    def _new_user(self) -> None:
        self._selected_user = None
        for row in self._user_rows:
            row.select(False)
        self._user_ctx.update("New User", "Fill in the form below to create an account")
        self.user_fullname.set("")
        self.user_username.set("")
        self.user_email.set("")
        roles = [r.name for r in self.auth_service.get_roles()]
        if roles:
            self.user_role.set(roles[0])
        self.user_password.set("")
        self.user_password_confirm.set("")
        self._toggle_btn.configure(text="Deactivate", style="danger")

    def _save_user(self) -> None:
        full_name = self.user_fullname.get()
        username = self.user_username.get()
        email = self.user_email.get()
        password = self.user_password.get()
        confirm = self.user_password_confirm.get()
        role_name = self.user_role.get()

        if not full_name or not username or not role_name:
            show_message(self, "Validation", "Full name, username and role are required.", "warning")
            return

        roles = {r.name: r.id for r in self.auth_service.get_roles()}
        if role_name not in roles:
            show_message(self, "Validation", "Select a valid role.", "warning")
            return

        if self._selected_user:
            if password or confirm:
                if password != confirm:
                    show_message(self, "Validation", "Passwords do not match.", "warning")
                    return
                if len(password) < 6:
                    show_message(self, "Validation", "Password must be at least 6 characters.", "warning")
                    return
            data = {
                "full_name": full_name,
                "username": username,
                "email": email or None,
                "role_id": roles[role_name],
            }
            if password:
                data["password"] = password
            ok, msg = self.auth_service.update_user(self._selected_user.id, data)
        else:
            if not password:
                show_message(self, "Validation", "Password is required for new users.", "warning")
                return
            if password != confirm:
                show_message(self, "Validation", "Passwords do not match.", "warning")
                return
            ok, msg, _ = self.auth_service.create_user({
                "full_name": full_name,
                "username": username,
                "email": email or None,
                "password": password,
                "role_id": roles[role_name],
                "is_active": True,
            })

        show_message(self, "Users", msg, "success" if ok else "error")
        if ok:
            self._refresh_users()
            if self._selected_user:
                updated = self.auth_service.user_repo.get_by_id(self._selected_user.id)
                if updated:
                    self._select_user(updated)

    def _reset_user_password(self) -> None:
        if not self._selected_user:
            show_message(self, "Users", "Select a user first.", "warning")
            return
        password = self.user_password.get()
        confirm = self.user_password_confirm.get()
        if not password:
            show_message(self, "Users", "Enter a new password in the Password field.", "warning")
            return
        if password != confirm:
            show_message(self, "Validation", "Passwords do not match.", "warning")
            return

        user = self._selected_user

        def do_reset():
            ok, msg = self.auth_service.reset_user_password(user.id, password)
            show_message(self, "Users", msg, "success" if ok else "error")
            if ok:
                self.user_password.set("")
                self.user_password_confirm.set("")

        _ConfirmDialog(
            self,
            title="Reset Password",
            message=f"Reset password for {user.full_name} (@{user.username})?",
            on_confirm=do_reset,
            confirm_label="Reset",
        )

    def _toggle_user_status(self) -> None:
        if not self._selected_user:
            show_message(self, "Users", "Select a user first.", "warning")
            return
        user = self._selected_user
        action = "activate" if not user.is_active else "deactivate"

        def do_toggle():
            ok, msg = self.auth_service.toggle_user_status(user.id)
            show_message(self, "Users", msg, "success" if ok else "error")
            if ok:
                updated = self.auth_service.user_repo.get_by_id(user.id)
                if updated:
                    self._select_user(updated)
                self._refresh_users()

        _ConfirmDialog(
            self,
            title=f"{action.capitalize()} User",
            message=f"{action.capitalize()} {user.full_name} (@{user.username})?",
            on_confirm=do_toggle,
            confirm_label=action.capitalize(),
        )

    # ── Permissions ───────────────────────────────────────────────────────────
    def _refresh_permission_users(self) -> None:
        self.permission_users = self.auth_service.get_all_users_with_roles()
        user_labels = [
            f"{user.username} — {user.full_name} ({user.role.name if user.role else 'No role'})"
            for user in self.permission_users
        ]
        self.permission_user_map = {
            label: user.id for label, user in zip(user_labels, self.permission_users)
        }
        self.permission_user_combo.configure(values=user_labels or ["No users available"])
        if user_labels:
            self.permission_user_combo.set(user_labels[0])
            self._load_user_permissions(user_labels[0])

    def _selected_permission_user_id(self) -> int | None:
        label = self.permission_user_combo.get()
        return self.permission_user_map.get(label)

    def _load_user_permissions(self, _selection: str | None = None) -> None:
        user_id = self._selected_permission_user_id()
        if not user_id:
            return
        user, permissions, uses_custom = self.auth_service.get_user_permissions(user_id)
        if not user:
            return
        for key, var in self.permission_vars.items():
            var.set(key in permissions)
        source = "custom permissions" if uses_custom else f"role defaults ({user.role.name if user.role else '—'})"
        self.permission_status.configure(text=f"Showing {source} for {user.full_name}.")

    def _save_user_permissions(self) -> None:
        user_id = self._selected_permission_user_id()
        if not user_id:
            show_message(self, "Permissions", "Select a user first.", "warning")
            return
        selected = [key for key, var in self.permission_vars.items() if var.get()]
        ok, msg = self.auth_service.update_user_permissions(user_id, selected)
        show_message(self, "Permissions", msg, "success" if ok else "error")
        if ok:
            self._load_user_permissions()

    def _reset_user_permissions(self) -> None:
        user_id = self._selected_permission_user_id()
        if not user_id:
            show_message(self, "Permissions", "Select a user first.", "warning")
            return
        ok, msg = self.auth_service.reset_user_permissions(user_id)
        show_message(self, "Permissions", msg, "success" if ok else "error")
        if ok:
            self._load_user_permissions()

    # ── Backup & logs ─────────────────────────────────────────────────────────
    def _refresh_logs(self) -> None:
        logs = self.settings_service.get_activity_logs_enriched(50)
        self._chip_log_count.set_value(str(len(logs)))

        for w in self._logs_scroll.winfo_children():
            w.destroy()

        if not logs:
            ctk.CTkLabel(
                self._logs_scroll, text="No activity logs yet.",
                font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED,
            ).pack(pady=20)
            return

        for log, username, full_name in logs:
            _LogRow(self._logs_scroll, log, username, full_name).pack(fill="x", pady=2)

    def _backup(self) -> None:
        ok, msg, path = self.settings_service.backup_database()
        show_message(self, "Backup", f"{msg}\n{path}" if path else msg, "success" if ok else "error")
        if ok:
            self._chip_backup_hint.set_value("Backed up")
            self._refresh_logs()

    def _restore(self) -> None:
        path = filedialog.askopenfilename(
            filetypes=[
                ("JSON backups", "*.json"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return

        def do_restore():
            ok, msg = self.settings_service.restore_database(path)
            show_message(self, "Restore", msg, "success" if ok else "error")

        _ConfirmDialog(
            self,
            title="Restore Database",
            message="This will overwrite current data. Continue?",
            on_confirm=do_restore,
            confirm_label="Restore",
        )

    # ── My account ────────────────────────────────────────────────────────────
    def _change_username(self) -> None:
        user = session_manager.get_current_user()
        if not user:
            return
        ok, msg = self.auth_service.change_username(user["id"], self.new_username.get())
        show_message(self, "Account", msg, "success" if ok else "error")

    def _change_password(self) -> None:
        user = session_manager.get_current_user()
        if not user:
            return
        ok, msg = self.auth_service.change_password(
            user["id"], self.current_password.get(), self.new_password.get()
        )
        show_message(self, "Account", msg, "success" if ok else "error")
