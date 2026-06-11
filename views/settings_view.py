"""Settings and administration view."""

import customtkinter as ctk
from tkinter import filedialog

from config.settings import PAGE_PERMISSIONS
from utils.security import session_manager
from utils.helpers import format_price_as_of
from views.components.theme import Theme
from views.components.widgets import ActionButton, DataTable, FormField, PageHeader, show_message


class SettingsView(ctk.CTkFrame):
    def __init__(self, master, settings_service, auth_service, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.settings_service = settings_service
        self.auth_service = auth_service
        self.grid_columnconfigure(0, weight=1)
        self._build_ui()
        self._load_settings()

    def _build_ui(self) -> None:
        PageHeader(self, "Settings", "Clinic configuration and system administration").grid(
            row=0, column=0, sticky="ew", pady=(0, 16)
        )

        tabs = ctk.CTkTabview(self, fg_color=Theme.CARD_BG, corner_radius=Theme.CORNER_RADIUS)
        tabs.grid(row=1, column=0, sticky="nsew")
        self.rowconfigure(1, weight=1)

        clinic_tab = tabs.add("Clinic Info")
        users_tab = tabs.add("Users")
        if session_manager.has_permission("users"):
            permissions_tab = tabs.add("Permissions")
            self._build_permissions_tab(permissions_tab)
        backup_tab = tabs.add("Backup & Logs")
        account_tab = tabs.add("My Account")

        self._build_clinic_tab(clinic_tab)
        self._build_users_tab(users_tab)
        self._build_backup_tab(backup_tab)
        self._build_account_tab(account_tab)

    def _build_clinic_tab(self, parent) -> None:
        parent.grid_columnconfigure((0, 1), weight=1)
        self.clinic_fields = {}
        fields = [
            ("clinic_name", "Clinic Name"), ("clinic_phone", "Phone"),
            ("clinic_email", "Email"), ("consultation_fee", "Consultation Fee"),
            ("tax_id", "Tax ID"), ("philhealth_accreditation", "PhilHealth Accreditation"),
        ]
        for i, (key, label) in enumerate(fields):
            ff = FormField(parent, label)
            ff.grid(row=i // 2, column=i % 2, sticky="ew", padx=16, pady=8)
            self.clinic_fields[key] = ff

        self.address_field = FormField(parent, "Address", "text")
        self.address_field.grid(row=3, column=0, columnspan=2, sticky="ew", padx=16, pady=8)
        self.receipt_header = FormField(parent, "Receipt Header", "text")
        self.receipt_header.grid(row=4, column=0, columnspan=2, sticky="ew", padx=16, pady=8)
        self.receipt_footer = FormField(parent, "Receipt Footer", "text")
        self.receipt_footer.grid(row=5, column=0, columnspan=2, sticky="ew", padx=16, pady=8)

        self.fee_asof_lbl = ctk.CTkLabel(
            parent, text="", font=Theme.FONT_TINY, text_color=Theme.TEXT_MUTED, anchor="w",
        )
        self.fee_asof_lbl.grid(row=6, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 4))

        ActionButton(parent, text="Save Settings", command=self._save_settings).grid(
            row=7, column=0, padx=16, pady=16, sticky="w"
        )

    def _build_permissions_tab(self, parent) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(
            parent,
            text="Choose which pages each user can access. Checked pages appear in that user's sidebar menu.",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_SECONDARY,
            anchor="w",
            wraplength=900,
            justify="left",
        ).grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))

        selector = ctk.CTkFrame(parent, fg_color="transparent")
        selector.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 12))
        selector.grid_columnconfigure(1, weight=1)

        self.permission_users = self.auth_service.get_all_users_with_roles()
        user_labels = [
            f"{user.username} — {user.full_name} ({user.role.name if user.role else 'No role'})"
            for user in self.permission_users
        ]
        self.permission_user_map = {label: user.id for label, user in zip(user_labels, self.permission_users)}

        ctk.CTkLabel(
            selector, text="Select User", font=Theme.FONT_BODY, text_color=Theme.TEXT_SECONDARY,
        ).grid(row=0, column=0, sticky="w", padx=(0, 12))
        self.permission_user_combo = ctk.CTkComboBox(
            selector, values=user_labels or ["No users available"],
            height=38, corner_radius=Theme.BUTTON_RADIUS, font=Theme.FONT_BODY,
            command=self._load_user_permissions,
        )
        self.permission_user_combo.grid(row=0, column=1, sticky="ew")
        if user_labels:
            self.permission_user_combo.set(user_labels[0])

        self.permission_status = ctk.CTkLabel(
            parent, text="", font=Theme.FONT_TINY, text_color=Theme.TEXT_MUTED, anchor="w",
        )
        self.permission_status.grid(row=2, column=0, sticky="nw", padx=16, pady=(0, 8))

        checks_frame = ctk.CTkScrollableFrame(
            parent, fg_color=Theme.SECONDARY, corner_radius=Theme.BUTTON_RADIUS,
        )
        checks_frame.grid(row=3, column=0, sticky="nsew", padx=16, pady=(0, 12))
        parent.grid_rowconfigure(3, weight=1)
        checks_frame.grid_columnconfigure((0, 1), weight=1)

        self.permission_vars = {}
        for index, (key, label) in enumerate(PAGE_PERMISSIONS):
            var = ctk.BooleanVar(value=False)
            self.permission_vars[key] = var
            ctk.CTkCheckBox(
                checks_frame,
                text=label,
                variable=var,
                font=Theme.FONT_BODY,
                text_color=Theme.TEXT_PRIMARY,
            ).grid(row=index // 2, column=index % 2, sticky="w", padx=16, pady=8)

        actions = ctk.CTkFrame(parent, fg_color="transparent")
        actions.grid(row=4, column=0, sticky="ew", padx=16, pady=(0, 16))
        ActionButton(actions, text="Save Permissions", command=self._save_user_permissions).pack(side="left", padx=(0, 8))
        ActionButton(
            actions, text="Reset to Role Defaults", style="secondary", command=self._reset_user_permissions,
        ).pack(side="left")

        if user_labels:
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
        self.permission_status.configure(text=f"Currently showing {source} for {user.full_name}.")

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

    def _build_users_tab(self, parent) -> None:
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        form = ctk.CTkFrame(parent, fg_color="transparent")
        form.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        form.grid_columnconfigure((0, 1, 2, 3), weight=1)

        roles = [r.name for r in self.auth_service.get_roles()]
        self.user_name = FormField(form, "Full Name")
        self.user_name.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        self.user_username = FormField(form, "Username")
        self.user_username.grid(row=0, column=1, sticky="ew", padx=8, pady=8)
        self.user_password = FormField(form, "Password")
        self.user_password.grid(row=0, column=2, sticky="ew", padx=8, pady=8)
        self.user_role = FormField(form, "Role", "combo", roles)
        self.user_role.grid(row=0, column=3, sticky="ew", padx=8, pady=8)
        ActionButton(form, text="Add User", command=self._add_user).grid(row=1, column=0, padx=8, pady=8)

        self.users_table = DataTable(parent, ["ID", "Username", "Full Name", "Role", "Status"])
        self.users_table.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)
        self._refresh_users()

    def _build_backup_tab(self, parent) -> None:
        parent.grid_columnconfigure(0, weight=1)
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=16)
        ActionButton(btn_frame, text="Backup Database", command=self._backup).pack(side="left", padx=(0, 8))
        ActionButton(btn_frame, text="Restore Database", style="secondary", command=self._restore).pack(side="left")

        self.logs_table = DataTable(parent, ["Date", "User", "Action", "Module", "Description"])
        self.logs_table.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        self._refresh_logs()

    def _build_account_tab(self, parent) -> None:
        parent.grid_columnconfigure(0, weight=1)
        self.new_username = FormField(parent, "New Username")
        self.new_username.grid(row=0, column=0, sticky="ew", padx=20, pady=12)
        self.current_password = FormField(parent, "Current Password")
        self.current_password.grid(row=1, column=0, sticky="ew", padx=20, pady=12)
        self.new_password = FormField(parent, "New Password")
        self.new_password.grid(row=2, column=0, sticky="ew", padx=20, pady=12)
        ActionButton(parent, text="Change Username", command=self._change_username).grid(row=3, column=0, padx=20, pady=8, sticky="w")
        ActionButton(parent, text="Change Password", command=self._change_password).grid(row=4, column=0, padx=20, pady=8, sticky="w")

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

    def _refresh_users(self) -> None:
        self.users_table.clear_rows()
        for u in self.auth_service.get_all_users():
            status = "Active" if u.is_active else "Inactive"
            role_name = u.role.name if u.role else "—"
            self.users_table.add_row([u.id, u.username, u.full_name, role_name, status])

    def _add_user(self) -> None:
        roles = {r.name: r.id for r in self.auth_service.get_roles()}
        role_name = self.user_role.get()
        if role_name not in roles:
            show_message(self, "Validation", "Select a valid role.", "warning")
            return
        ok, msg, _ = self.auth_service.create_user({
            "full_name": self.user_name.get(),
            "username": self.user_username.get(),
            "password": self.user_password.get(),
            "role_id": roles[role_name],
            "is_active": True,
        })
        show_message(self, "Users", msg, "success" if ok else "error")
        if ok:
            self._refresh_users()

    def _backup(self) -> None:
        ok, msg, path = self.settings_service.backup_database()
        show_message(self, "Backup", f"{msg}\n{path}" if path else msg, "success" if ok else "error")

    def _restore(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("SQL files", "*.sql")])
        if not path:
            return
        ok, msg = self.settings_service.restore_database(path)
        show_message(self, "Restore", msg, "success" if ok else "error")

    def _refresh_logs(self) -> None:
        self.logs_table.clear_rows()
        for log in self.settings_service.get_activity_logs(50):
            self.logs_table.add_row([
                str(log.created_at)[:19], str(log.user_id or "—"),
                log.action, log.module or "—", (log.description or "")[:60],
            ])

    def _change_username(self) -> None:
        from utils.security import session_manager
        user = session_manager.get_current_user()
        if not user:
            return
        ok, msg = self.auth_service.change_username(user["id"], self.new_username.get())
        show_message(self, "Account", msg, "success" if ok else "error")

    def _change_password(self) -> None:
        from utils.security import session_manager
        user = session_manager.get_current_user()
        if not user:
            return
        ok, msg = self.auth_service.change_password(
            user["id"], self.current_password.get(), self.new_password.get()
        )
        show_message(self, "Account", msg, "success" if ok else "error")
