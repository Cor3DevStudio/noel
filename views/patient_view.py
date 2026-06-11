"""Patient management view — dashboard design standard."""

import customtkinter as ctk

from utils.helpers import calculate_age
from utils.validators import parse_date, sanitize_string
from views.components.theme import Theme
from views.components.widgets import ActionButton, FormField, PanelCard, SearchBar, show_message


# ─────────────────────────────────────────────────────────────────────────────
#  Stat chip — compact KPI card for the list header
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
#  Patient list row — styled card with hover + selection
# ─────────────────────────────────────────────────────────────────────────────
class _PatientRow(ctk.CTkFrame):
    def __init__(self, master, patient, on_select, **kwargs):
        super().__init__(
            master, fg_color="transparent", corner_radius=8,
            cursor="hand2", **kwargs,
        )
        self._patient = patient
        self._on_select = on_select
        self._selected = False

        self._bar = ctk.CTkFrame(self, fg_color="transparent", width=3, corner_radius=2)
        self._bar.pack(side="left", fill="y", padx=(4, 0))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(side="left", fill="both", expand=True, padx=(10, 12), pady=3)

        top = ctk.CTkFrame(body, fg_color="transparent")
        top.pack(fill="x")
        self._name_lbl = ctk.CTkLabel(
            top, text=patient.full_name,
            font=("Segoe UI", 11, "bold"), text_color=Theme.TEXT_PRIMARY, anchor="w",
        )
        self._name_lbl.pack(side="left")
        ctk.CTkLabel(
            top, text=patient.patient_number,
            font=Theme.FONT_TINY, text_color=Theme.TEXT_MUTED, anchor="e",
        ).pack(side="right")

        sub = ctk.CTkFrame(body, fg_color="transparent")
        sub.pack(fill="x")
        age = calculate_age(patient.birth_date) if patient.birth_date else "—"
        ph  = patient.philhealth_number or "No PhilHealth"
        ctk.CTkLabel(
            sub, text=f"{patient.gender or '—'}  ·  Age {age}  ·  {ph}",
            font=Theme.FONT_TINY, text_color=Theme.TEXT_SECONDARY, anchor="w",
        ).pack(side="left")

        if patient.is_senior_citizen:
            ctk.CTkLabel(sub, text="SC", font=("Segoe UI", 9, "bold"),
                         text_color=Theme.SUCCESS).pack(side="right", padx=(4, 0))
        if patient.is_pwd:
            ctk.CTkLabel(sub, text="PWD", font=("Segoe UI", 9, "bold"),
                         text_color=Theme.PURPLE).pack(side="right", padx=(4, 0))

        for w in self._collect_widgets(self):
            w.bind("<Button-1>", lambda _e: self._click())
            w.bind("<Enter>",    lambda _e: self._hover(True))
            w.bind("<Leave>",    lambda _e: self._hover(False))

    def _collect_widgets(self, root):
        yield root
        for child in root.winfo_children():
            yield from self._collect_widgets(child)

    def _click(self) -> None:
        self._on_select(self._patient)

    def _hover(self, on: bool) -> None:
        if not self._selected:
            self.configure(fg_color=Theme.SECONDARY if on else "transparent")

    def select(self, active: bool) -> None:
        self._selected = active
        self.configure(fg_color=Theme.ACCENT_LIGHT if active else "transparent")
        self._bar.configure(fg_color=Theme.ACCENT if active else "transparent")
        self._name_lbl.configure(
            text_color=Theme.ACCENT if active else Theme.TEXT_PRIMARY
        )


# ─────────────────────────────────────────────────────────────────────────────
#  Profile header card — selected patient summary
# ─────────────────────────────────────────────────────────────────────────────
class _ProfileCard(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(
            master, fg_color=Theme.CARD_BG,
            corner_radius=Theme.CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER, **kwargs,
        )
        ctk.CTkFrame(self, fg_color=Theme.ACCENT, width=4, corner_radius=0).pack(
            side="left", fill="y"
        )
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(side="left", fill="both", expand=True, padx=16, pady=14)

        top = ctk.CTkFrame(body, fg_color="transparent")
        top.pack(fill="x")

        self._avatar_box = ctk.CTkFrame(
            top, fg_color=Theme.ACCENT_LIGHT, width=46, height=46, corner_radius=23,
        )
        self._avatar_box.pack(side="left")
        self._avatar_box.pack_propagate(False)
        self._avatar_lbl = ctk.CTkLabel(
            self._avatar_box, text="?",
            font=("Segoe UI", 17, "bold"), text_color=Theme.ACCENT,
        )
        self._avatar_lbl.place(relx=0.5, rely=0.5, anchor="center")

        info = ctk.CTkFrame(top, fg_color="transparent")
        info.pack(side="left", padx=(14, 0))
        self._name_lbl = ctk.CTkLabel(
            info, text="No patient selected",
            font=Theme.FONT_SUBHEADING, text_color=Theme.TEXT_PRIMARY, anchor="w",
        )
        self._name_lbl.pack(anchor="w")
        self._sub_lbl = ctk.CTkLabel(
            info, text="Select from the list or register a new patient",
            font=Theme.FONT_TINY, text_color=Theme.TEXT_MUTED, anchor="w",
        )
        self._sub_lbl.pack(anchor="w")

        self._badge_row = ctk.CTkFrame(body, fg_color="transparent")
        self._badge_row.pack(fill="x", pady=(8, 0))

    def refresh(self, patient) -> None:
        for w in self._badge_row.winfo_children():
            w.destroy()

        if patient is None:
            self._avatar_lbl.configure(text="?")
            self._name_lbl.configure(text="No patient selected")
            self._sub_lbl.configure(text="Select from the list or register a new patient")
            return

        initials = "".join(p[0].upper() for p in patient.full_name.split()[:2])
        self._avatar_lbl.configure(text=initials)
        self._name_lbl.configure(text=patient.full_name)

        age_str = ""
        if patient.birth_date:
            a = calculate_age(patient.birth_date)
            age_str = f"  ·  Age {a}" if a else ""
        self._sub_lbl.configure(
            text=f"{patient.patient_number}  ·  {patient.gender or '—'}{age_str}"
        )

        def _badge(text, color, tint):
            b = ctk.CTkFrame(self._badge_row, fg_color=tint, corner_radius=6)
            b.pack(side="left", padx=(0, 6))
            ctk.CTkLabel(b, text=text, font=Theme.FONT_TINY, text_color=color).pack(
                padx=8, pady=3
            )

        ph = patient.philhealth_number or "No PhilHealth"
        _badge(f"PH: {ph}", Theme.ACCENT, Theme.ACCENT_LIGHT)
        if patient.philhealth_member_type:
            _badge(patient.philhealth_member_type, "#0891B2", "#ECFEFF")
        if patient.is_senior_citizen:
            _badge("Senior Citizen", Theme.SUCCESS, Theme.SUCCESS_LIGHT)
        if patient.is_pwd:
            _badge("PWD", Theme.PURPLE, Theme.PURPLE_LIGHT)


# ─────────────────────────────────────────────────────────────────────────────
#  Main Patient View
# ─────────────────────────────────────────────────────────────────────────────
class PatientView(ctk.CTkFrame):
    def __init__(self, master, patient_service, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.service = patient_service
        self.selected_patient = None
        self._row_widgets: list[_PatientRow] = []

        self.grid_columnconfigure(0, weight=5)
        self.grid_columnconfigure(1, weight=8)
        self.grid_rowconfigure(0, weight=1)

        self._build_list_panel()
        self._build_form_panel()
        self.refresh_list()

    # ── Left: patient list ────────────────────────────────────────────────────
    def _build_list_panel(self) -> None:
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(2, weight=1)

        # ── Stat chips ────────────────────────────────────────────────────────
        chips = ctk.CTkFrame(left, fg_color="transparent")
        chips.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        chips.grid_columnconfigure((0, 1, 2), weight=1)

        self._chip_total  = _StatChip(chips, "Total Patients", Theme.ACCENT,   Theme.ACCENT_LIGHT)
        self._chip_senior = _StatChip(chips, "Senior Citizens", Theme.SUCCESS,  Theme.SUCCESS_LIGHT)
        self._chip_pwd    = _StatChip(chips, "PWD Patients",    Theme.PURPLE,   Theme.PURPLE_LIGHT)
        self._chip_total.grid( row=0, column=0, sticky="ew", padx=(0, 4))
        self._chip_senior.grid(row=0, column=1, sticky="ew", padx=4)
        self._chip_pwd.grid(   row=0, column=2, sticky="ew", padx=(4, 0))

        # ── Search ────────────────────────────────────────────────────────────
        self._search = SearchBar(
            left, "Search name, ID, PhilHealth...",
            on_search=self.refresh_list,
        )
        self._search.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        # ── Patient list ──────────────────────────────────────────────────────
        list_card = ctk.CTkFrame(
            left, fg_color=Theme.CARD_BG,
            corner_radius=Theme.CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER,
        )
        list_card.grid(row=2, column=0, sticky="nsew")
        list_card.grid_columnconfigure(0, weight=1)
        list_card.grid_rowconfigure(1, weight=1)

        list_hdr = ctk.CTkFrame(list_card, fg_color=Theme.SECONDARY, corner_radius=0, height=38)
        list_hdr.grid(row=0, column=0, sticky="ew")
        list_hdr.grid_propagate(False)
        list_hdr.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            list_hdr, text="Patient Records",
            font=Theme.FONT_SUBHEADING, text_color=Theme.TEXT_PRIMARY, anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=14, pady=8)

        self._list_scroll = ctk.CTkScrollableFrame(
            list_card, fg_color="transparent",
        )
        self._list_scroll.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)

        # ── Toolbar ───────────────────────────────────────────────────────────
        toolbar = ctk.CTkFrame(left, fg_color="transparent")
        toolbar.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        ActionButton(toolbar, text="+ New Patient",
                     command=self._clear_form).pack(side="left", padx=(0, 8))
        ActionButton(toolbar, text="Archive Patient", style="danger",
                     command=self._archive).pack(side="left", padx=(0, 8))
        ActionButton(toolbar, text="Refresh", style="secondary",
                     command=lambda: self.refresh_list()).pack(side="left")

    # ── Right: form panel ─────────────────────────────────────────────────────
    def _build_form_panel(self) -> None:
        self._form_scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
        )
        self._form_scroll.grid(row=0, column=1, sticky="nsew")
        self._form_scroll.grid_columnconfigure(0, weight=1)

        self.fields: dict[str, FormField] = {}

        # Profile card
        self._profile_card = _ProfileCard(self._form_scroll)
        self._profile_card.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # ── Section 1: Personal Information ───────────────────────────────────
        p1 = PanelCard(self._form_scroll, "Personal Information", "Name, birth date & contact details")
        p1.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        p1.body.grid_columnconfigure((0, 1), weight=1)

        personal_fields = [
            ("first_name",     "First Name *",          "entry", None),
            ("middle_name",    "Middle Name",            "entry", None),
            ("last_name",      "Last Name *",            "entry", None),
            ("suffix",         "Suffix",                 "entry", None),
            ("birth_date",     "Birth Date (YYYY-MM-DD)","entry", None),
            ("gender",         "Gender",                 "combo", ["Male", "Female", "Other"]),
            ("civil_status",   "Civil Status",           "combo", ["Single", "Married", "Widowed", "Separated", "Divorced"]),
            ("contact_number", "Contact Number",         "entry", None),
            ("email",          "Email Address",          "entry", None),
        ]
        self._place_fields(p1.body, personal_fields, start_row=0)

        # ── Section 2: Address & Emergency Contact ────────────────────────────
        p2 = PanelCard(self._form_scroll, "Address & Emergency Contact", "Home address and emergency information")
        p2.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        p2.body.grid_columnconfigure((0, 1), weight=1)

        address_fields = [
            ("address_street",              "Street Address",       "entry", None),
            ("address_barangay",            "Barangay",             "entry", None),
            ("address_city",                "City / Municipality",  "entry", None),
            ("address_province",            "Province",             "entry", None),
            ("emergency_contact_name",      "Emergency Contact Name","entry", None),
            ("emergency_contact_relationship","Relationship",        "entry", None),
            ("emergency_contact_phone",     "Emergency Phone",      "entry", None),
        ]
        self._place_fields(p2.body, address_fields, start_row=0)

        # ── Section 3: PhilHealth & Classification ────────────────────────────
        p3 = PanelCard(self._form_scroll, "PhilHealth & Classification", "Member details and special classifications")
        p3.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        p3.body.grid_columnconfigure((0, 1), weight=1)

        ph_fields = [
            ("philhealth_number",      "PhilHealth Number",  "entry", None),
            ("philhealth_category",    "PhilHealth Category","combo",
             ["Employed", "Self-Employed", "Indigent", "Senior Citizen", "OFW", "Retired", "Other"]),
            ("philhealth_member_type", "Member Type",        "combo",
             ["Member", "Dependent"]),
        ]
        self._place_fields(p3.body, ph_fields, start_row=0)

        # Senior & PWD flags row
        flags_row = ctk.CTkFrame(p3.body, fg_color="transparent")
        flags_row.grid(row=2, column=0, columnspan=2, sticky="ew", padx=4, pady=(4, 0))
        flags_row.grid_columnconfigure((0, 1), weight=1)

        self.senior_var = ctk.BooleanVar()
        self.pwd_var    = ctk.BooleanVar()

        sc_frame = ctk.CTkFrame(flags_row, fg_color="transparent")
        sc_frame.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkCheckBox(
            sc_frame, text="Senior Citizen",
            variable=self.senior_var,
            fg_color=Theme.SUCCESS, hover_color="#059669",
            font=Theme.FONT_BODY,
        ).pack(anchor="w", pady=(0, 4))
        self.fields["senior_id_number"] = FormField(sc_frame, "Senior ID Number")
        self.fields["senior_id_number"].pack(fill="x")

        pwd_frame = ctk.CTkFrame(flags_row, fg_color="transparent")
        pwd_frame.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        ctk.CTkCheckBox(
            pwd_frame, text="PWD",
            variable=self.pwd_var,
            fg_color=Theme.PURPLE, hover_color="#7C3AED",
            font=Theme.FONT_BODY,
        ).pack(anchor="w", pady=(0, 4))
        self.fields["pwd_id_number"] = FormField(pwd_frame, "PWD ID Number")
        self.fields["pwd_id_number"].pack(fill="x")

        # ── Duplicate name warning banner (hidden by default) ─────────────────
        self._dup_banner = ctk.CTkFrame(
            self._form_scroll,
            fg_color=Theme.DANGER_LIGHT,
            corner_radius=Theme.CORNER_RADIUS,
            border_width=1, border_color=Theme.DANGER,
        )
        # not gridded until a duplicate is found

        dup_inner = ctk.CTkFrame(self._dup_banner, fg_color="transparent")
        dup_inner.pack(fill="x", padx=14, pady=10)
        ctk.CTkLabel(
            dup_inner,
            text="⚠  Duplicate Name Detected",
            font=("Segoe UI", 12, "bold"),
            text_color=Theme.DANGER, anchor="w",
        ).pack(anchor="w")
        self._dup_detail = ctk.CTkLabel(
            dup_inner, text="",
            font=Theme.FONT_TINY, text_color=Theme.DANGER,
            anchor="w", wraplength=480, justify="left",
        )
        self._dup_detail.pack(anchor="w", pady=(2, 0))

        # ── Footer buttons ────────────────────────────────────────────────────
        footer = ctk.CTkFrame(self._form_scroll, fg_color="transparent")
        footer.grid(row=5, column=0, sticky="ew", pady=(4, 0))
        ActionButton(footer, text="Save Patient",
                     command=self._save).pack(side="left", padx=(0, 8))
        ActionButton(footer, text="Clear Form", style="secondary",
                     command=self._clear_form).pack(side="left")

    # ── Helper: place FormField grid in a panel body ──────────────────────────
    def _place_fields(self, parent, field_defs: list, start_row: int) -> None:
        for i, (key, label, wtype, values) in enumerate(field_defs):
            row = start_row + i // 2
            col = i % 2
            px_l = 0 if col == 0 else 6
            px_r = 6 if col == 0 else 0
            ff = FormField(parent, label, wtype, values)
            ff.grid(row=row, column=col, sticky="ew", padx=(px_l, px_r), pady=4)
            self.fields[key] = ff
            # Bind live duplicate check on first/last name blur
            if key in ("first_name", "last_name"):
                ff.widget.bind("<FocusOut>", lambda _e: self._check_duplicate_live())

    # ── Live duplicate name check ─────────────────────────────────────────────
    def _check_duplicate_live(self) -> None:
        fn_field = self.fields.get("first_name")
        ln_field = self.fields.get("last_name")
        first = sanitize_string(fn_field.get() if fn_field else "")
        last  = sanitize_string(ln_field.get() if ln_field else "")
        if not first or not last:
            self._hide_dup_banner()
            return

        exclude_id = self.selected_patient.id if self.selected_patient else None
        duplicates = self.service.repo.find_by_name(first, last, exclude_id=exclude_id)

        if duplicates:
            lines = "\n".join(
                f"  •  {p.full_name}  ({p.patient_number})  —  {p.contact_number or 'no contact'}"
                for p in duplicates
            )
            self._dup_detail.configure(
                text=f"An existing patient with this name was found:\n{lines}\n"
                     f"Verify this is a different person before saving."
            )
            self._dup_banner.grid(row=4, column=0, sticky="ew", pady=(0, 8))
        else:
            self._hide_dup_banner()

    def _hide_dup_banner(self) -> None:
        self._dup_banner.grid_forget()

    # ── List refresh ──────────────────────────────────────────────────────────
    def refresh_list(self, query: str = "") -> None:
        q = query or self._search.get()
        patients = self.service.search(q)

        for w in self._list_scroll.winfo_children():
            w.destroy()
        self._row_widgets.clear()

        total  = len(patients)
        senior = sum(1 for p in patients if p.is_senior_citizen)
        pwd    = sum(1 for p in patients if p.is_pwd)

        self._chip_total.set_value(str(total))
        self._chip_senior.set_value(str(senior))
        self._chip_pwd.set_value(str(pwd))

        if not patients:
            ctk.CTkLabel(
                self._list_scroll, text="No patients found.",
                font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED,
            ).pack(pady=20)
            return

        for i, p in enumerate(patients):
            row_widget = _PatientRow(
                self._list_scroll, p,
                on_select=self._on_row_select,
            )
            row_widget.pack(fill="x", padx=2)

            # Thin divider between rows
            ctk.CTkFrame(
                self._list_scroll, fg_color=Theme.BORDER, height=1,
            ).pack(fill="x", padx=6)

            self._row_widgets.append(row_widget)

        # Re-highlight if a patient was already selected
        if self.selected_patient:
            for rw in self._row_widgets:
                if rw._patient.id == self.selected_patient.id:
                    rw.select(True)

    def _on_row_select(self, patient) -> None:
        for rw in self._row_widgets:
            rw.select(rw._patient.id == patient.id)
        self._load_patient(patient.id)

    # ── Load patient into form ────────────────────────────────────────────────
    def _load_patient(self, patient_id: int) -> None:
        patient = self.service.get_by_id(patient_id)
        if not patient:
            return
        self.selected_patient = patient
        self._profile_card.refresh(patient)

        for key, field in self.fields.items():
            val = getattr(patient, key, None)
            field.set(str(val) if val else "")

        self.senior_var.set(patient.is_senior_citizen)
        self.pwd_var.set(patient.is_pwd)

    # ── Form data collection ──────────────────────────────────────────────────
    def _collect_data(self) -> dict:
        data = {k: sanitize_string(f.get()) for k, f in self.fields.items()}
        data["birth_date"]        = parse_date(data.get("birth_date", ""))
        data["is_senior_citizen"] = self.senior_var.get()
        data["is_pwd"]            = self.pwd_var.get()
        data["gender"]            = data.get("gender") or "Other"
        return data

    # ── Save ─────────────────────────────────────────────────────────────────
    def _save(self) -> None:
        data = self._collect_data()
        if not data.get("first_name") or not data.get("last_name"):
            show_message(self, "Validation", "First name and last name are required.", "warning")
            return
        if self.selected_patient:
            ok, msg = self.service.update(self.selected_patient.id, data)
        else:
            ok, msg, patient = self.service.register(data)
            if ok:
                self.selected_patient = patient
        show_message(self, "Patients", msg, "success" if ok else "error")
        if ok:
            self._hide_dup_banner()
            self.refresh_list()
            if self.selected_patient:
                self._profile_card.refresh(self.service.get_by_id(self.selected_patient.id))

    # ── Archive ───────────────────────────────────────────────────────────────
    def _archive(self) -> None:
        if not self.selected_patient:
            show_message(self, "Archive", "Select a patient first.", "warning")
            return
        ok, msg = self.service.archive(self.selected_patient.id)
        show_message(self, "Archive", msg, "success" if ok else "error")
        if ok:
            self._clear_form()
            self.refresh_list()

    # ── Clear form ────────────────────────────────────────────────────────────
    def _clear_form(self) -> None:
        self.selected_patient = None
        self._profile_card.refresh(None)
        self._hide_dup_banner()
        for field in self.fields.values():
            field.set("")
        self.senior_var.set(False)
        self.pwd_var.set(False)
        for rw in self._row_widgets:
            rw.select(False)

    def refresh(self) -> None:
        self.refresh_list()
