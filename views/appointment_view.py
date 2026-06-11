"""Appointment management view."""

import customtkinter as ctk
from datetime import date, datetime

from views.components.theme import Theme
from views.components.widgets import ActionButton, DataTable, FormField, PageHeader, show_message


class AppointmentView(ctk.CTkFrame):
    def __init__(self, master, appointment_service, patient_service, user_service, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.appointment_service = appointment_service
        self.patient_service = patient_service
        self.user_service = user_service
        self.selected_id = None
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        PageHeader(self, "Appointments", "Schedule and manage appointments").grid(
            row=0, column=0, sticky="ew", pady=(0, 16)
        )

        form = ctk.CTkFrame(
            self, fg_color=Theme.CARD_BG, corner_radius=Theme.CORNER_RADIUS,
            border_width=1, border_color=Theme.BORDER,
        )
        form.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        form.grid_columnconfigure((0, 1, 2, 3), weight=1)

        patients = [f"{p.id} - {p.full_name}" for p in self.patient_service.search("")]
        doctors = [f"{d.id} - {d.full_name}" for d in self.user_service.get_doctors()]

        self.patient_field = FormField(form, "Patient", "combo", patients or ["No patients"])
        self.patient_field.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        self.doctor_field = FormField(form, "Doctor", "combo", doctors or ["No doctors"])
        self.doctor_field.grid(row=0, column=1, sticky="ew", padx=12, pady=12)
        self.date_field = FormField(form, "Date (YYYY-MM-DD)")
        self.date_field.set(str(date.today()))
        self.date_field.grid(row=0, column=2, sticky="ew", padx=12, pady=12)
        self.time_field = FormField(form, "Time (HH:MM)")
        self.time_field.set("09:00")
        self.time_field.grid(row=0, column=3, sticky="ew", padx=12, pady=12)

        self.reason_field = FormField(form, "Reason")
        self.reason_field.grid(row=1, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 12))
        self.status_field = FormField(
            form, "Status", "combo",
            ["Scheduled", "Confirmed", "Completed", "Cancelled", "No Show"],
        )
        self.status_field.grid(row=1, column=2, sticky="ew", padx=12, pady=(0, 12))

        btn_row = ctk.CTkFrame(form, fg_color="transparent")
        btn_row.grid(row=1, column=3, sticky="e", padx=12, pady=(0, 12))
        ActionButton(btn_row, text="Save", command=self._save).pack(side="left", padx=4)
        ActionButton(btn_row, text="Cancel Appt", style="danger", command=self._cancel).pack(side="left", padx=4)
        ActionButton(btn_row, text="New", style="secondary", command=self._clear).pack(side="left")

        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.grid(row=2, column=0, sticky="new", pady=(0, 8))
        self.filter_date = FormField(filter_frame, "View Date")
        self.filter_date.set(str(date.today()))
        self.filter_date.pack(side="left", padx=(0, 8))
        ActionButton(filter_frame, text="Load Schedule", command=self.refresh).pack(side="left")

        self.table = DataTable(self, ["ID", "Time", "Patient", "Doctor", "Reason", "Status"])
        self.table.grid(row=3, column=0, sticky="nsew")
        self.rowconfigure(3, weight=1)

    def refresh(self) -> None:
        from utils.validators import parse_date
        target = parse_date(self.filter_date.get()) or date.today()
        appointments = self.appointment_service.get_by_date(target)
        self.table.clear_rows()
        for a in appointments:
            patient_name = a.patient.full_name if a.patient else "—"
            doctor_name = a.doctor.full_name if a.doctor else "—"
            self.table.add_row(
                [a.id, str(a.appointment_time)[:5], patient_name, doctor_name, a.reason or "—", a.status],
                on_click=lambda aid=a.id: self._load(aid),
            )

    def _parse_id(self, combo_val: str) -> int | None:
        try:
            return int(combo_val.split(" - ")[0])
        except (ValueError, IndexError):
            return None

    def _save(self) -> None:
        from utils.validators import parse_date
        patient_id = self._parse_id(self.patient_field.get())
        if not patient_id:
            show_message(self, "Validation", "Select a valid patient.", "warning")
            return
        appt_date = parse_date(self.date_field.get())
        if not appt_date:
            show_message(self, "Validation", "Invalid date format.", "warning")
            return
        try:
            appt_time = datetime.strptime(self.time_field.get(), "%H:%M").time()
        except ValueError:
            show_message(self, "Validation", "Invalid time format (use HH:MM).", "warning")
            return

        data = {
            "patient_id": patient_id,
            "doctor_id": self._parse_id(self.doctor_field.get()),
            "appointment_date": appt_date,
            "appointment_time": appt_time,
            "reason": self.reason_field.get(),
            "status": self.status_field.get() or "Scheduled",
        }
        if self.selected_id:
            ok, msg = self.appointment_service.update(self.selected_id, data)
        else:
            ok, msg, _ = self.appointment_service.create(data)
        show_message(self, "Appointments", msg, "success" if ok else "error")
        if ok:
            self.refresh()

    def _cancel(self) -> None:
        if not self.selected_id:
            show_message(self, "Cancel", "Select an appointment first.", "warning")
            return
        ok, msg = self.appointment_service.cancel(self.selected_id)
        show_message(self, "Appointments", msg, "success" if ok else "error")
        if ok:
            self.refresh()

    def _load(self, appt_id: int) -> None:
        appt = self.appointment_service.get_by_id(appt_id)
        if not appt:
            return
        self.selected_id = appt_id
        if appt.patient:
            self.patient_field.set(f"{appt.patient_id} - {appt.patient.full_name}")
        if appt.doctor:
            self.doctor_field.set(f"{appt.doctor_id} - {appt.doctor.full_name}")
        self.date_field.set(str(appt.appointment_date))
        self.time_field.set(str(appt.appointment_time)[:5])
        self.reason_field.set(appt.reason or "")
        self.status_field.set(appt.status)

    def _clear(self) -> None:
        self.selected_id = None
        self.date_field.set(str(date.today()))
        self.time_field.set("09:00")
        self.reason_field.set("")
        self.status_field.set("Scheduled")
