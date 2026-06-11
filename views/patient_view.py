"""Patient management view."""

import customtkinter as ctk
from tkinter import filedialog

from utils.helpers import calculate_age, format_date
from utils.validators import parse_date, sanitize_string
from views.components.theme import Theme
from views.components.widgets import ActionButton, DataTable, FormField, PageHeader, SearchBar, show_message


class PatientView(ctk.CTkFrame):
    def __init__(self, master, patient_service, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.service = patient_service
        self.selected_patient = None
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(1, weight=1)
        self._build_list_panel()
        self._build_form_panel()
        self.refresh_list()

    def _build_list_panel(self) -> None:
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 12))
        left.grid_rowconfigure(2, weight=1)
        left.grid_columnconfigure(0, weight=1)

        PageHeader(left, "Patients", "Manage patient records").grid(row=0, column=0, sticky="ew", pady=(0, 12))
        self.search = SearchBar(left, "Search by name, ID, PhilHealth...", on_search=self.refresh_list)
        self.search.grid(row=1, column=0, sticky="ew", pady=(0, 12))

        self.table = DataTable(left, ["ID", "Patient No.", "Name", "Contact"])
        self.table.grid(row=2, column=0, sticky="nsew")

        btn_frame = ctk.CTkFrame(left, fg_color="transparent")
        btn_frame.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        ActionButton(btn_frame, text="New Patient", command=self._clear_form).pack(side="left", padx=(0, 8))
        ActionButton(btn_frame, text="Refresh", style="secondary", command=self.refresh_list).pack(side="left")

    def _build_form_panel(self) -> None:
        right = ctk.CTkScrollableFrame(
            self, fg_color=Theme.CARD_BG, corner_radius=Theme.CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER,
        )
        right.grid(row=0, column=1, rowspan=2, sticky="nsew")
        right.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(
            right, text="Patient Information", font=Theme.FONT_HEADING, text_color=Theme.TEXT_PRIMARY
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(20, 16))

        fields = [
            ("first_name", "First Name *"), ("middle_name", "Middle Name"),
            ("last_name", "Last Name *"), ("suffix", "Suffix"),
            ("birth_date", "Birth Date (YYYY-MM-DD)"), ("gender", "Gender", "combo", ["Male", "Female", "Other"]),
            ("contact_number", "Contact Number"), ("email", "Email"),
            ("address_street", "Street Address"), ("address_barangay", "Barangay"),
            ("address_city", "City"), ("address_province", "Province"),
            ("emergency_contact_name", "Emergency Contact"), ("emergency_contact_phone", "Emergency Phone"),
            ("philhealth_number", "PhilHealth Number"), ("philhealth_category", "PhilHealth Category"),
            ("senior_id_number", "Senior ID Number"), ("pwd_id_number", "PWD ID Number"),
        ]
        self.fields = {}
        for i, field_def in enumerate(fields):
            key = field_def[0]
            label = field_def[1]
            wtype = field_def[2] if len(field_def) > 2 else "entry"
            values = field_def[3] if len(field_def) > 3 else None
            row, col = divmod(i, 2)
            ff = FormField(right, label, wtype, values)
            ff.grid(row=row + 1, column=col, sticky="ew", padx=(20 if col == 0 else 10, 20 if col == 1 else 10), pady=6)
            self.fields[key] = ff

        self.senior_var = ctk.BooleanVar()
        self.pwd_var = ctk.BooleanVar()
        flags = ctk.CTkFrame(right, fg_color="transparent")
        flags.grid(row=10, column=0, columnspan=2, sticky="w", padx=20, pady=8)
        ctk.CTkCheckBox(flags, text="Senior Citizen", variable=self.senior_var).pack(side="left", padx=(0, 20))
        ctk.CTkCheckBox(flags, text="PWD", variable=self.pwd_var).pack(side="left")

        btn_row = ctk.CTkFrame(right, fg_color="transparent")
        btn_row.grid(row=11, column=0, columnspan=2, sticky="ew", padx=20, pady=20)
        ActionButton(btn_row, text="Save Patient", command=self._save).pack(side="left", padx=(0, 8))
        ActionButton(btn_row, text="Archive", style="danger", command=self._archive).pack(side="left", padx=(0, 8))
        ActionButton(btn_row, text="Clear", style="secondary", command=self._clear_form).pack(side="left")

    def refresh_list(self, query: str = "") -> None:
        patients = self.service.search(query or self.search.get())
        self.table.clear_rows()
        for p in patients:
            self.table.add_row(
                [p.id, p.patient_number, p.full_name, p.contact_number or "—"],
                on_click=lambda pid=p.id: self._load_patient(pid),
            )

    def _load_patient(self, patient_id: int) -> None:
        patient = self.service.get_by_id(patient_id)
        if not patient:
            return
        self.selected_patient = patient
        for key, field in self.fields.items():
            val = getattr(patient, key, "")
            if key == "birth_date" and val:
                field.set(str(val))
            else:
                field.set(str(val) if val else "")
        self.senior_var.set(patient.is_senior_citizen)
        self.pwd_var.set(patient.is_pwd)

    def _collect_data(self) -> dict:
        data = {key: sanitize_string(field.get()) for key, field in self.fields.items()}
        data["birth_date"] = parse_date(data.get("birth_date", ""))
        data["is_senior_citizen"] = self.senior_var.get()
        data["is_pwd"] = self.pwd_var.get()
        data["gender"] = data.get("gender") or "Other"
        return data

    def _save(self) -> None:
        data = self._collect_data()
        if not data["first_name"] or not data["last_name"]:
            show_message(self, "Validation", "First and last name are required.", "warning")
            return
        if self.selected_patient:
            ok, msg = self.service.update(self.selected_patient.id, data)
        else:
            ok, msg, patient = self.service.register(data)
            if ok:
                self.selected_patient = patient
        show_message(self, "Patients", msg, "success" if ok else "error")
        if ok:
            self.refresh_list()

    def _archive(self) -> None:
        if not self.selected_patient:
            show_message(self, "Archive", "Select a patient first.", "warning")
            return
        ok, msg = self.service.archive(self.selected_patient.id)
        show_message(self, "Archive", msg, "success" if ok else "error")
        if ok:
            self._clear_form()
            self.refresh_list()

    def _clear_form(self) -> None:
        self.selected_patient = None
        for field in self.fields.values():
            field.set("")
        self.senior_var.set(False)
        self.pwd_var.set(False)
