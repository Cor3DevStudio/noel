"""Consultation and prescription view — dashboard design standard."""

import customtkinter as ctk

from views.components.theme import Theme
from views.components.widgets import ActionButton, FormField, PanelCard, show_message


_STATUS_COLOR = {
    "Active":    (Theme.ACCENT,  Theme.ACCENT_LIGHT),
    "Completed": (Theme.SUCCESS, Theme.SUCCESS_LIGHT),
    "Cancelled": (Theme.DANGER,  Theme.DANGER_LIGHT),
}


# ─────────────────────────────────────────────────────────────────────────────
class _StatChip(ctk.CTkFrame):
    def __init__(self, master, label: str, color: str, tint: str, **kwargs):
        super().__init__(master, fg_color=tint, corner_radius=10,
                         border_width=1, border_color=color, **kwargs)
        self._val = ctk.CTkLabel(self, text="—", font=("Segoe UI", 20, "bold"), text_color=color)
        self._val.pack(padx=14, pady=(10, 0), anchor="w")
        ctk.CTkLabel(self, text=label, font=Theme.FONT_TINY,
                     text_color=Theme.TEXT_MUTED).pack(padx=14, pady=(0, 10), anchor="w")

    def set_value(self, v: str) -> None:
        self._val.configure(text=v)


# ─────────────────────────────────────────────────────────────────────────────
class _ConsultRow(ctk.CTkFrame):
    """Compact single-click consultation history row."""

    def __init__(self, master, consult, patient_name: str, on_select, **kwargs):
        super().__init__(master, fg_color="transparent", corner_radius=8,
                         cursor="hand2", **kwargs)
        self._consult = consult
        self._on_select = on_select
        self._selected = False

        color, tint = _STATUS_COLOR.get(consult.status, ("#6B7280", "#F3F4F6"))

        self._bar = ctk.CTkFrame(self, fg_color="transparent", width=3, corner_radius=2)
        self._bar.pack(side="left", fill="y", padx=(4, 0))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(side="left", fill="both", expand=True, padx=(10, 12), pady=5)

        top = ctk.CTkFrame(body, fg_color="transparent")
        top.pack(fill="x")

        self._name_lbl = ctk.CTkLabel(
            top, text=patient_name,
            font=("Segoe UI", 11, "bold"), text_color=Theme.TEXT_PRIMARY, anchor="w",
        )
        self._name_lbl.pack(side="left")

        badge = ctk.CTkFrame(top, fg_color=tint, corner_radius=5)
        badge.pack(side="right")
        ctk.CTkLabel(badge, text=consult.status, font=Theme.FONT_TINY,
                     text_color=color).pack(padx=7, pady=2)

        sub = ctk.CTkFrame(body, fg_color="transparent")
        sub.pack(fill="x")
        date_str = str(consult.consultation_date)[:16] if consult.consultation_date else "—"
        diag = (consult.diagnosis or "No diagnosis recorded")[:50]
        ctk.CTkLabel(sub, text=f"{date_str}  ·  {diag}",
                     font=Theme.FONT_TINY, text_color=Theme.TEXT_SECONDARY, anchor="w").pack(side="left")

        for w in self._walk(self):
            w.bind("<Button-1>", lambda _e: self._click())
            w.bind("<Enter>",    lambda _e: self._hover(True))
            w.bind("<Leave>",    lambda _e: self._hover(False))

    def _walk(self, root):
        yield root
        for c in root.winfo_children():
            yield from self._walk(c)

    def _click(self):
        self._on_select(self._consult)

    def _hover(self, on: bool):
        if not self._selected:
            self.configure(fg_color=Theme.SECONDARY if on else "transparent")

    def select(self, active: bool):
        self._selected = active
        color, _ = _STATUS_COLOR.get(self._consult.status, ("#6B7280", "#F3F4F6"))
        self.configure(fg_color=Theme.ACCENT_LIGHT if active else "transparent")
        self._bar.configure(fg_color=color if active else "transparent")
        self._name_lbl.configure(text_color=Theme.ACCENT if active else Theme.TEXT_PRIMARY)


# ─────────────────────────────────────────────────────────────────────────────
class _PatientHeaderCard(ctk.CTkFrame):
    """Patient summary card shown at top of consultation form."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=Theme.CARD_BG, corner_radius=Theme.CORNER_RADIUS,
                         border_width=1, border_color=Theme.BORDER, **kwargs)
        self._bar = ctk.CTkFrame(self, fg_color=Theme.PURPLE, width=4, corner_radius=0)
        self._bar.pack(side="left", fill="y")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(side="left", fill="both", expand=True, padx=16, pady=12)

        top = ctk.CTkFrame(body, fg_color="transparent")
        top.pack(fill="x")

        self._avatar = ctk.CTkFrame(top, fg_color=Theme.PURPLE_LIGHT,
                                     width=42, height=42, corner_radius=21)
        self._avatar.pack(side="left")
        self._avatar.pack_propagate(False)
        self._avatar_lbl = ctk.CTkLabel(self._avatar, text="?",
                                         font=("Segoe UI", 15, "bold"), text_color=Theme.PURPLE)
        self._avatar_lbl.place(relx=0.5, rely=0.5, anchor="center")

        info = ctk.CTkFrame(top, fg_color="transparent")
        info.pack(side="left", padx=(12, 0))
        self._name = ctk.CTkLabel(info, text="No patient selected",
                                   font=Theme.FONT_SUBHEADING, text_color=Theme.TEXT_PRIMARY, anchor="w")
        self._name.pack(anchor="w")
        self._sub = ctk.CTkLabel(info, text="Select a patient and load their history",
                                  font=Theme.FONT_TINY, text_color=Theme.TEXT_MUTED, anchor="w")
        self._sub.pack(anchor="w")

        self._badge_row = ctk.CTkFrame(body, fg_color="transparent")
        self._badge_row.pack(fill="x", pady=(6, 0))

    def update(self, patient) -> None:
        for w in self._badge_row.winfo_children():
            w.destroy()
        if patient is None:
            self._avatar_lbl.configure(text="?")
            self._name.configure(text="No patient selected")
            self._sub.configure(text="Select a patient and load their history")
            return

        initials = "".join(p[0].upper() for p in patient.full_name.split()[:2])
        self._avatar_lbl.configure(text=initials)
        self._name.configure(text=patient.full_name)
        ph = patient.philhealth_number or "No PhilHealth"
        self._sub.configure(text=f"{patient.patient_number}  ·  {patient.gender or '—'}  ·  PH: {ph}")

        def _badge(text, color, tint):
            b = ctk.CTkFrame(self._badge_row, fg_color=tint, corner_radius=6)
            b.pack(side="left", padx=(0, 6))
            ctk.CTkLabel(b, text=text, font=Theme.FONT_TINY, text_color=color).pack(padx=8, pady=3)

        if patient.is_senior_citizen:
            _badge("Senior Citizen", Theme.SUCCESS, Theme.SUCCESS_LIGHT)
        if patient.is_pwd:
            _badge("PWD", Theme.PURPLE, Theme.PURPLE_LIGHT)
        if patient.philhealth_member_type:
            _badge(patient.philhealth_member_type, "#0891B2", "#ECFEFF")


# ─────────────────────────────────────────────────────────────────────────────
class ConsultationView(ctk.CTkFrame):
    def __init__(self, master, consultation_service, patient_service, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.consultation_service = consultation_service
        self.patient_service = patient_service
        self.selected_id = None
        self._selected_patient = None
        self._row_widgets: list[_ConsultRow] = []

        self.grid_columnconfigure(0, weight=5)
        self.grid_columnconfigure(1, weight=7)
        self.grid_rowconfigure(0, weight=1)

        self._build_list_panel()
        self._build_form_panel()
        self._patient_combo_loaded = False

    # ── Left panel ────────────────────────────────────────────────────────────
    def _build_list_panel(self) -> None:
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(2, weight=1)

        # Stat chips
        chips = ctk.CTkFrame(left, fg_color="transparent")
        chips.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        chips.grid_columnconfigure((0, 1, 2), weight=1)
        self._chip_total     = _StatChip(chips, "Loaded",       Theme.PURPLE,  Theme.PURPLE_LIGHT)
        self._chip_active    = _StatChip(chips, "Active",        Theme.ACCENT,  Theme.ACCENT_LIGHT)
        self._chip_completed = _StatChip(chips, "Completed",     Theme.SUCCESS, Theme.SUCCESS_LIGHT)
        self._chip_total.grid(    row=0, column=0, sticky="ew", padx=(0, 4))
        self._chip_active.grid(   row=0, column=1, sticky="ew", padx=4)
        self._chip_completed.grid(row=0, column=2, sticky="ew", padx=(4, 0))

        # Patient search bar
        search_bar = ctk.CTkFrame(left, fg_color="transparent")
        search_bar.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        search_bar.grid_columnconfigure(0, weight=1)

        self._patient_combo = ctk.CTkComboBox(
            search_bar, values=["— load on refresh —"],
            height=38, font=Theme.FONT_BODY, corner_radius=Theme.BUTTON_RADIUS,
            border_color=Theme.BORDER,
        )
        self._patient_combo.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ActionButton(search_bar, text="Load History", command=self._load_history).grid(row=0, column=1)

        # Consultation list card
        list_card = ctk.CTkFrame(left, fg_color=Theme.CARD_BG, corner_radius=Theme.CORNER_RADIUS,
                                  border_width=1, border_color=Theme.BORDER)
        list_card.grid(row=2, column=0, sticky="nsew")
        list_card.grid_columnconfigure(0, weight=1)
        list_card.grid_rowconfigure(1, weight=1)

        hdr = ctk.CTkFrame(list_card, fg_color=Theme.SECONDARY, corner_radius=0, height=38)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)
        ctk.CTkLabel(hdr, text="Consultation History", font=Theme.FONT_SUBHEADING,
                     text_color=Theme.TEXT_PRIMARY, anchor="w").pack(side="left", padx=14, pady=8)

        self._list_scroll = ctk.CTkScrollableFrame(list_card, fg_color="transparent")
        self._list_scroll.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)

        # Toolbar
        toolbar = ctk.CTkFrame(left, fg_color="transparent")
        toolbar.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        ActionButton(toolbar, text="+ New Consultation", command=self._clear).pack(side="left", padx=(0, 8))
        ActionButton(toolbar, text="Mark Complete", style="success", command=self._complete).pack(side="left", padx=(0, 8))
        ActionButton(toolbar, text="Refresh", style="secondary", command=self._load_history).pack(side="left")

    # ── Right panel ───────────────────────────────────────────────────────────
    def _build_form_panel(self) -> None:
        right = ctk.CTkScrollableFrame(self, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)

        # Patient header card
        self._patient_card = _PatientHeaderCard(right)
        self._patient_card.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # ── Vitals panel ──────────────────────────────────────────────────────
        vitals_panel = PanelCard(right, "Vital Signs", "Measured at time of visit")
        vitals_panel.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        vitals_panel.body.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.bp_field   = FormField(vitals_panel.body, "Blood Pressure")
        self.bp_field.grid(  row=0, column=0, sticky="ew", padx=(0, 6), pady=4)
        self.hr_field   = FormField(vitals_panel.body, "Heart Rate (bpm)")
        self.hr_field.grid(  row=0, column=1, sticky="ew", padx=6, pady=4)
        self.temp_field = FormField(vitals_panel.body, "Temperature (°C)")
        self.temp_field.grid(row=0, column=2, sticky="ew", padx=6, pady=4)
        self.wt_field   = FormField(vitals_panel.body, "Weight (kg)")
        self.wt_field.grid(  row=0, column=3, sticky="ew", padx=(6, 0), pady=4)

        # ── Clinical notes panel ──────────────────────────────────────────────
        notes_panel = PanelCard(right, "Clinical Notes", "Complaint, diagnosis and treatment plan")
        notes_panel.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        notes_panel.body.grid_columnconfigure((0, 1), weight=1)

        self.complaint_field = FormField(notes_panel.body, "Chief Complaint", "text")
        self.complaint_field.grid(row=0, column=0, sticky="ew", padx=(0, 6), pady=4)
        self.diagnosis_field = FormField(notes_panel.body, "Diagnosis", "text")
        self.diagnosis_field.grid(row=0, column=1, sticky="ew", padx=(6, 0), pady=4)
        self.treatment_field = FormField(notes_panel.body, "Treatment Plan", "text")
        self.treatment_field.grid(row=1, column=0, sticky="ew", padx=(0, 6), pady=4)
        self.notes_field     = FormField(notes_panel.body, "Doctor Notes", "text")
        self.notes_field.grid(    row=1, column=1, sticky="ew", padx=(6, 0), pady=4)

        # ── Patient selector (for new consultation) ───────────────────────────
        assign_panel = PanelCard(right, "Patient Assignment", "Assign this consultation record to a patient")
        assign_panel.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        assign_panel.body.grid_columnconfigure(0, weight=1)

        patients = [f"{p.id} - {p.full_name}" for p in self.patient_service.search("")]
        self.patient_field = FormField(assign_panel.body, "Patient *", "combo", patients or ["No patients"])
        self.patient_field.grid(row=0, column=0, sticky="ew", pady=4)

        # Footer
        footer = ctk.CTkFrame(right, fg_color="transparent")
        footer.grid(row=4, column=0, sticky="ew", pady=(0, 4))
        ActionButton(footer, text="Save Consultation", command=self._save).pack(side="left", padx=(0, 8))
        ActionButton(footer, text="Mark Complete", style="success", command=self._complete).pack(side="left", padx=(0, 8))
        ActionButton(footer, text="Clear", style="secondary", command=self._clear).pack(side="left")

    # ── Load patient history ──────────────────────────────────────────────────
    def _load_history(self) -> None:
        patient_id = self._parse_patient_id(self._patient_combo.get())
        if not patient_id:
            show_message(self, "History", "Select a patient first.", "warning")
            return

        patient = self.patient_service.get_by_id(patient_id)
        self._selected_patient = patient
        self._patient_card.update(patient)

        # Pre-fill patient combo in form panel
        if patient:
            self.patient_field.set(f"{patient.id} - {patient.full_name}")

        records = self.consultation_service.get_by_patient(patient_id)

        for w in self._list_scroll.winfo_children():
            w.destroy()
        self._row_widgets.clear()

        total     = len(records)
        active    = sum(1 for r in records if r.status == "Active")
        completed = sum(1 for r in records if r.status == "Completed")
        self._chip_total.set_value(str(total))
        self._chip_active.set_value(str(active))
        self._chip_completed.set_value(str(completed))

        if not records:
            ctk.CTkLabel(self._list_scroll, text="No consultations found for this patient.",
                         font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(pady=20)
            return

        patient_name = patient.full_name if patient else "—"
        for c in records:
            rw = _ConsultRow(self._list_scroll, c, patient_name, on_select=self._on_row_select)
            rw.pack(fill="x", padx=2)
            ctk.CTkFrame(self._list_scroll, fg_color=Theme.BORDER, height=1).pack(fill="x", padx=6)
            self._row_widgets.append(rw)

    # ── Row select ────────────────────────────────────────────────────────────
    def _on_row_select(self, consult) -> None:
        for rw in self._row_widgets:
            rw.select(rw._consult.id == consult.id)
        self._load_consultation(consult.id)

    def _load_consultation(self, consult_id: int) -> None:
        c = self.consultation_service.get_with_details(consult_id)
        if not c:
            return
        self.selected_id = c.id

        patient = self.patient_service.get_by_id(c.patient_id)
        if patient:
            self._patient_card.update(patient)
            self.patient_field.set(f"{c.patient_id} - {patient.full_name}")

        self.complaint_field.set(c.chief_complaint or "")
        self.diagnosis_field.set(c.diagnosis or "")
        self.treatment_field.set(c.treatment_plan or "")
        self.notes_field.set(c.doctor_notes or "")

        vs = c.vital_signs or {}
        self.bp_field.set(vs.get("blood_pressure", ""))
        self.hr_field.set(vs.get("heart_rate", ""))
        self.temp_field.set(vs.get("temperature", ""))
        self.wt_field.set(vs.get("weight", ""))

    # ── Save ─────────────────────────────────────────────────────────────────
    def _save(self) -> None:
        patient_id = self._parse_patient_id(self.patient_field.get())
        if not patient_id:
            show_message(self, "Validation", "Select a patient.", "warning")
            return

        vitals = {
            "blood_pressure": self.bp_field.get(),
            "heart_rate":     self.hr_field.get(),
            "temperature":    self.temp_field.get(),
            "weight":         self.wt_field.get(),
        }
        data = {
            "patient_id":     patient_id,
            "chief_complaint": self.complaint_field.get(),
            "diagnosis":       self.diagnosis_field.get(),
            "treatment_plan":  self.treatment_field.get(),
            "doctor_notes":    self.notes_field.get(),
            "vital_signs":     vitals,
        }
        if self.selected_id:
            ok, msg = self.consultation_service.update(self.selected_id, data)
        else:
            ok, msg, consult = self.consultation_service.create(data)
            if ok:
                self.selected_id = consult.id

        show_message(self, "Consultations", msg, "success" if ok else "error")
        if ok:
            self._load_history()

    # ── Complete ──────────────────────────────────────────────────────────────
    def _complete(self) -> None:
        if not self.selected_id:
            show_message(self, "Complete", "Save or select a consultation first.", "warning")
            return
        ok, msg = self.consultation_service.complete(self.selected_id)
        show_message(self, "Consultations", msg, "success" if ok else "error")
        if ok:
            self._load_history()

    # ── Clear ─────────────────────────────────────────────────────────────────
    def _clear(self) -> None:
        self.selected_id = None
        for f in (self.complaint_field, self.diagnosis_field,
                  self.treatment_field, self.notes_field,
                  self.bp_field, self.hr_field, self.temp_field, self.wt_field):
            f.set("")
        for rw in self._row_widgets:
            rw.select(False)

    # ── Helpers ───────────────────────────────────────────────────────────────
    @staticmethod
    def _parse_patient_id(val: str) -> int | None:
        try:
            return int(val.split(" - ")[0])
        except (ValueError, IndexError):
            return None

    def refresh(self) -> None:
        if not self._patient_combo_loaded:
            patients = [f"{p.id} - {p.full_name}" for p in self.patient_service.search("")]
            self._patient_combo.configure(values=patients or ["No patients"])
            self._patient_combo_loaded = True
