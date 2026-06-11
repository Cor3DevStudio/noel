"""Consultation and prescription view."""

import customtkinter as ctk

from views.components.theme import Theme
from views.components.widgets import ActionButton, DataTable, FormField, PageHeader, show_message


class ConsultationView(ctk.CTkFrame):
    def __init__(self, master, consultation_service, patient_service, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.consultation_service = consultation_service
        self.patient_service = patient_service
        self.selected_id = None
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self._build_ui()

    def _build_ui(self) -> None:
        PageHeader(self, "Consultations", "Medical consultation records").grid(
            row=0, column=0, sticky="ew", pady=(0, 16)
        )

        form = ctk.CTkFrame(
            self, fg_color=Theme.CARD_BG, corner_radius=Theme.CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER,
        )
        form.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        form.grid_columnconfigure((0, 1), weight=1)

        patients = [f"{p.id} - {p.full_name}" for p in self.patient_service.search("")]
        self.patient_field = FormField(form, "Patient", "combo", patients or ["No patients"])
        self.patient_field.grid(row=0, column=0, sticky="ew", padx=16, pady=12)
        self.complaint_field = FormField(form, "Chief Complaint", "text")
        self.complaint_field.grid(row=0, column=1, sticky="ew", padx=16, pady=12)
        self.diagnosis_field = FormField(form, "Diagnosis", "text")
        self.diagnosis_field.grid(row=1, column=0, sticky="ew", padx=16, pady=12)
        self.treatment_field = FormField(form, "Treatment Plan", "text")
        self.treatment_field.grid(row=1, column=1, sticky="ew", padx=16, pady=12)
        self.notes_field = FormField(form, "Doctor Notes", "text")
        self.notes_field.grid(row=2, column=0, columnspan=2, sticky="ew", padx=16, pady=12)

        vitals = ctk.CTkFrame(form, fg_color="transparent")
        vitals.grid(row=3, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 12))
        vitals.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self.bp_field = FormField(vitals, "Blood Pressure")
        self.bp_field.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.hr_field = FormField(vitals, "Heart Rate")
        self.hr_field.grid(row=0, column=1, sticky="ew", padx=8)
        self.temp_field = FormField(vitals, "Temperature")
        self.temp_field.grid(row=0, column=2, sticky="ew", padx=8)
        self.weight_field = FormField(vitals, "Weight (kg)")
        self.weight_field.grid(row=0, column=3, sticky="ew", padx=(8, 0))

        btn_row = ctk.CTkFrame(form, fg_color="transparent")
        btn_row.grid(row=4, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 16))
        ActionButton(btn_row, text="Save Consultation", command=self._save).pack(side="left", padx=(0, 8))
        ActionButton(btn_row, text="Complete", style="success", command=self._complete).pack(side="left", padx=(0, 8))
        ActionButton(btn_row, text="Load History", style="secondary", command=self._load_history).pack(side="left")

        self.table = DataTable(self, ["ID", "Date", "Patient", "Diagnosis", "Status"])
        self.table.grid(row=2, column=0, sticky="nsew")

    def _parse_patient_id(self) -> int | None:
        try:
            return int(self.patient_field.get().split(" - ")[0])
        except (ValueError, IndexError):
            return None

    def _save(self) -> None:
        patient_id = self._parse_patient_id()
        if not patient_id:
            show_message(self, "Validation", "Select a patient.", "warning")
            return
        vitals = {
            "blood_pressure": self.bp_field.get(),
            "heart_rate": self.hr_field.get(),
            "temperature": self.temp_field.get(),
            "weight": self.weight_field.get(),
        }
        data = {
            "patient_id": patient_id,
            "chief_complaint": self.complaint_field.get(),
            "diagnosis": self.diagnosis_field.get(),
            "treatment_plan": self.treatment_field.get(),
            "doctor_notes": self.notes_field.get(),
            "vital_signs": vitals,
        }
        if self.selected_id:
            ok, msg = self.consultation_service.update(self.selected_id, data)
        else:
            ok, msg, consult = self.consultation_service.create(data)
            if ok:
                self.selected_id = consult.id
        show_message(self, "Consultations", msg, "success" if ok else "error")

    def _complete(self) -> None:
        if not self.selected_id:
            show_message(self, "Complete", "Save consultation first.", "warning")
            return
        ok, msg = self.consultation_service.complete(self.selected_id)
        show_message(self, "Consultations", msg, "success" if ok else "error")

    def _load_history(self) -> None:
        patient_id = self._parse_patient_id()
        if not patient_id:
            show_message(self, "History", "Select a patient.", "warning")
            return
        records = self.consultation_service.get_by_patient(patient_id)
        self.table.clear_rows()
        for c in records:
            patient = self.patient_service.get_by_id(c.patient_id)
            name = patient.full_name if patient else "—"
            self.table.add_row(
                [c.id, str(c.consultation_date)[:16], name, (c.diagnosis or "—")[:40], c.status],
                on_click=lambda cid=c.id: self._load_consultation(cid),
            )

    def _load_consultation(self, consult_id: int) -> None:
        c = self.consultation_service.get_with_details(consult_id)
        if not c:
            return
        self.selected_id = c.id
        patient = self.patient_service.get_by_id(c.patient_id)
        if patient:
            self.patient_field.set(f"{c.patient_id} - {patient.full_name}")
        self.complaint_field.set(c.chief_complaint or "")
        self.diagnosis_field.set(c.diagnosis or "")
        self.treatment_field.set(c.treatment_plan or "")
        self.notes_field.set(c.doctor_notes or "")
        if c.vital_signs:
            self.bp_field.set(c.vital_signs.get("blood_pressure", ""))
            self.hr_field.set(c.vital_signs.get("heart_rate", ""))
            self.temp_field.set(c.vital_signs.get("temperature", ""))
            self.weight_field.set(c.vital_signs.get("weight", ""))
