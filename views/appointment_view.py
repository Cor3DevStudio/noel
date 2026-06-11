"""Appointment management view — dashboard design standard."""

import customtkinter as ctk
from datetime import date, datetime

from utils.validators import parse_date
from views.components.theme import Theme
from views.components.widgets import ActionButton, FormField, PanelCard, show_message


_STATUS_COLOR = {
    "Scheduled": (Theme.ACCENT,   Theme.ACCENT_LIGHT),
    "Confirmed":  (Theme.SUCCESS,  Theme.SUCCESS_LIGHT),
    "Completed":  ("#6B7280",     "#F3F4F6"),
    "Cancelled":  (Theme.DANGER,  Theme.DANGER_LIGHT),
    "No Show":    (Theme.WARNING, Theme.WARNING_LIGHT),
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
class _ContextCard(ctk.CTkFrame):
    """Accent-bar header showing current selection context."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=Theme.CARD_BG, corner_radius=Theme.CORNER_RADIUS,
                         border_width=1, border_color=Theme.BORDER, **kwargs)
        self._bar = ctk.CTkFrame(self, fg_color=Theme.ACCENT, width=4, corner_radius=0)
        self._bar.pack(side="left", fill="y")
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(side="left", fill="both", expand=True, padx=16, pady=12)
        self._title = ctk.CTkLabel(body, text="No appointment selected",
                                   font=Theme.FONT_SUBHEADING, text_color=Theme.TEXT_PRIMARY, anchor="w")
        self._title.pack(anchor="w")
        self._sub = ctk.CTkLabel(body, text="Select from the schedule or create a new appointment",
                                 font=Theme.FONT_TINY, text_color=Theme.TEXT_MUTED, anchor="w")
        self._sub.pack(anchor="w")

    def update(self, title: str, sub: str, status: str = "") -> None:
        color, _ = _STATUS_COLOR.get(status, (Theme.ACCENT, Theme.ACCENT_LIGHT))
        self._bar.configure(fg_color=color)
        self._title.configure(text=title)
        self._sub.configure(text=sub)


# ─────────────────────────────────────────────────────────────────────────────
class _ApptRow(ctk.CTkFrame):
    """Compact single-click appointment row."""

    def __init__(self, master, appt, on_select, **kwargs):
        super().__init__(master, fg_color="transparent", corner_radius=8,
                         cursor="hand2", **kwargs)
        self._appt = appt
        self._on_select = on_select
        self._selected = False

        color, tint = _STATUS_COLOR.get(appt.status, ("#6B7280", "#F3F4F6"))

        self._bar = ctk.CTkFrame(self, fg_color="transparent", width=3, corner_radius=2)
        self._bar.pack(side="left", fill="y", padx=(4, 0))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(side="left", fill="both", expand=True, padx=(10, 12), pady=5)

        top = ctk.CTkFrame(body, fg_color="transparent")
        top.pack(fill="x")

        time_str = str(appt.appointment_time)[:5] if appt.appointment_time else "—:—"
        self._time_lbl = ctk.CTkLabel(top, text=time_str,
                                       font=("Segoe UI", 12, "bold"), text_color=color,
                                       anchor="w", width=44)
        self._time_lbl.pack(side="left")

        patient_name = appt.patient.full_name if appt.patient else "—"
        self._name_lbl = ctk.CTkLabel(top, text=patient_name,
                                       font=("Segoe UI", 11, "bold"),
                                       text_color=Theme.TEXT_PRIMARY, anchor="w")
        self._name_lbl.pack(side="left", padx=(8, 0))

        badge_frame = ctk.CTkFrame(top, fg_color=tint, corner_radius=5)
        badge_frame.pack(side="right")
        ctk.CTkLabel(badge_frame, text=appt.status, font=Theme.FONT_TINY,
                     text_color=color).pack(padx=7, pady=2)

        sub = ctk.CTkFrame(body, fg_color="transparent")
        sub.pack(fill="x")
        doctor = appt.doctor.full_name if appt.doctor else "No doctor assigned"
        reason = (appt.reason or "No reason")[:48]
        ctk.CTkLabel(sub, text=f"{doctor}  ·  {reason}",
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
        self._on_select(self._appt)

    def _hover(self, on: bool):
        if not self._selected:
            self.configure(fg_color=Theme.SECONDARY if on else "transparent")

    def select(self, active: bool):
        self._selected = active
        color, _ = _STATUS_COLOR.get(self._appt.status, ("#6B7280", "#F3F4F6"))
        self.configure(fg_color=Theme.ACCENT_LIGHT if active else "transparent")
        self._bar.configure(fg_color=color if active else "transparent")
        self._name_lbl.configure(text_color=Theme.ACCENT if active else Theme.TEXT_PRIMARY)


# ─────────────────────────────────────────────────────────────────────────────
class AppointmentView(ctk.CTkFrame):
    def __init__(self, master, appointment_service, patient_service, user_service, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.appointment_service = appointment_service
        self.patient_service = patient_service
        self.user_service = user_service
        self.selected_id = None
        self._row_widgets: list[_ApptRow] = []

        self.grid_columnconfigure(0, weight=5)
        self.grid_columnconfigure(1, weight=7)
        self.grid_rowconfigure(0, weight=1)

        self._build_list_panel()
        self._build_form_panel()
        self._form_choices_loaded = False

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
        self._chip_total     = _StatChip(chips, "Today Total",   Theme.ACCENT,  Theme.ACCENT_LIGHT)
        self._chip_scheduled = _StatChip(chips, "Scheduled",     Theme.PURPLE,  Theme.PURPLE_LIGHT)
        self._chip_confirmed = _StatChip(chips, "Confirmed",     Theme.SUCCESS, Theme.SUCCESS_LIGHT)
        self._chip_total.grid(    row=0, column=0, sticky="ew", padx=(0, 4))
        self._chip_scheduled.grid(row=0, column=1, sticky="ew", padx=4)
        self._chip_confirmed.grid(row=0, column=2, sticky="ew", padx=(4, 0))

        # Date filter bar
        date_bar = ctk.CTkFrame(left, fg_color="transparent")
        date_bar.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        date_bar.grid_columnconfigure(0, weight=1)
        self._filter_date = ctk.CTkEntry(
            date_bar, placeholder_text="YYYY-MM-DD",
            height=38, font=Theme.FONT_BODY, corner_radius=Theme.BUTTON_RADIUS,
            border_color=Theme.BORDER,
        )
        self._filter_date.insert(0, str(date.today()))
        self._filter_date.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self._filter_date.bind("<Return>", lambda _e: self.refresh())
        ActionButton(date_bar, text="Load Day", command=self.refresh).grid(row=0, column=1)

        # List card
        list_card = ctk.CTkFrame(left, fg_color=Theme.CARD_BG, corner_radius=Theme.CORNER_RADIUS,
                                  border_width=1, border_color=Theme.BORDER)
        list_card.grid(row=2, column=0, sticky="nsew")
        list_card.grid_columnconfigure(0, weight=1)
        list_card.grid_rowconfigure(1, weight=1)

        hdr = ctk.CTkFrame(list_card, fg_color=Theme.SECONDARY, corner_radius=0, height=38)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)
        hdr.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(hdr, text="Daily Schedule", font=Theme.FONT_SUBHEADING,
                     text_color=Theme.TEXT_PRIMARY, anchor="w").grid(row=0, column=0, sticky="w", padx=14)

        self._list_scroll = ctk.CTkScrollableFrame(list_card, fg_color="transparent")
        self._list_scroll.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)

        # Toolbar
        toolbar = ctk.CTkFrame(left, fg_color="transparent")
        toolbar.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        ActionButton(toolbar, text="+ New Appointment", command=self._clear).pack(side="left", padx=(0, 8))
        ActionButton(toolbar, text="Cancel Appointment", style="danger", command=self._cancel).pack(side="left", padx=(0, 8))
        ActionButton(toolbar, text="Refresh", style="secondary", command=self.refresh).pack(side="left")

    # ── Right panel ───────────────────────────────────────────────────────────
    def _build_form_panel(self) -> None:
        right = ctk.CTkScrollableFrame(self, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)

        # Context card
        self._ctx = _ContextCard(right)
        self._ctx.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # Details form
        details = PanelCard(right, "Appointment Details", "Patient, schedule, doctor & status")
        details.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        details.body.grid_columnconfigure((0, 1), weight=1)

        self.patient_field = FormField(details.body, "Patient *", "combo", ["— load on refresh —"])
        self.doctor_field  = FormField(details.body, "Attending Doctor", "combo", ["— load on refresh —"])
        self.patient_field.grid(row=0, column=0, sticky="ew", padx=(0, 6), pady=4)
        self.doctor_field.grid(row=0, column=1, sticky="ew", padx=(6, 0), pady=4)
        self.date_field    = FormField(details.body, "Appointment Date (YYYY-MM-DD)")
        self.date_field.set(str(date.today()))
        self.date_field.grid(   row=1, column=0, sticky="ew", padx=(0, 6), pady=4)
        self.time_field    = FormField(details.body, "Time (HH:MM)")
        self.time_field.set("09:00")
        self.time_field.grid(   row=1, column=1, sticky="ew", padx=(6, 0), pady=4)
        self.reason_field  = FormField(details.body, "Reason / Chief Complaint")
        self.reason_field.grid( row=2, column=0, columnspan=2, sticky="ew", pady=4)
        self.status_field  = FormField(details.body, "Status", "combo",
                                       ["Scheduled", "Confirmed", "Completed", "Cancelled", "No Show"])
        self.status_field.set("Scheduled")
        self.status_field.grid( row=3, column=0, sticky="ew", padx=(0, 6), pady=4)

        # Status legend
        legend = ctk.CTkFrame(details.body, fg_color="transparent")
        legend.grid(row=3, column=1, sticky="ew", padx=(6, 0), pady=4)
        ctk.CTkLabel(legend, text="Status Guide", font=Theme.FONT_TINY,
                     text_color=Theme.TEXT_MUTED, anchor="w").pack(anchor="w")
        for status, (color, tint) in _STATUS_COLOR.items():
            row = ctk.CTkFrame(legend, fg_color="transparent")
            row.pack(anchor="w")
            ctk.CTkFrame(row, fg_color=color, width=8, height=8, corner_radius=4).pack(side="left", padx=(0, 4))
            ctk.CTkLabel(row, text=status, font=Theme.FONT_TINY,
                         text_color=Theme.TEXT_SECONDARY).pack(side="left")

        # Footer
        footer = ctk.CTkFrame(right, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", pady=(0, 4))
        ActionButton(footer, text="Save Appointment", command=self._save).pack(side="left", padx=(0, 8))
        ActionButton(footer, text="Clear Form", style="secondary", command=self._clear).pack(side="left")

    # ── Refresh ───────────────────────────────────────────────────────────────
    def refresh(self) -> None:
        if not self._form_choices_loaded:
            patients = [f"{p.id} - {p.full_name}" for p in self.patient_service.search("")]
            doctors = [f"{d.id} - {d.full_name}" for d in self.user_service.get_doctors()]
            self.patient_field.set_values(patients or ["No patients"])
            self.doctor_field.set_values(doctors or ["No doctors"])
            self._form_choices_loaded = True

        target = parse_date(self._filter_date.get().strip()) or date.today()
        appointments = self.appointment_service.get_by_date(target)

        total     = len(appointments)
        scheduled = sum(1 for a in appointments if a.status == "Scheduled")
        confirmed = sum(1 for a in appointments if a.status == "Confirmed")
        self._chip_total.set_value(str(total))
        self._chip_scheduled.set_value(str(scheduled))
        self._chip_confirmed.set_value(str(confirmed))

        for w in self._list_scroll.winfo_children():
            w.destroy()
        self._row_widgets.clear()

        if not appointments:
            ctk.CTkLabel(self._list_scroll, text="No appointments for this date.",
                         font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED).pack(pady=20)
            return

        for appt in appointments:
            rw = _ApptRow(self._list_scroll, appt, on_select=self._on_row_select)
            rw.pack(fill="x", padx=2)
            ctk.CTkFrame(self._list_scroll, fg_color=Theme.BORDER, height=1).pack(fill="x", padx=6)
            self._row_widgets.append(rw)

        if self.selected_id:
            for rw in self._row_widgets:
                if rw._appt.id == self.selected_id:
                    rw.select(True)

    # ── Row select ────────────────────────────────────────────────────────────
    def _on_row_select(self, appt) -> None:
        for rw in self._row_widgets:
            rw.select(rw._appt.id == appt.id)
        self._load(appt.id)

    def _load(self, appt_id: int) -> None:
        appt = self.appointment_service.get_by_id(appt_id)
        if not appt:
            return
        self.selected_id = appt_id
        patient_name = appt.patient.full_name if appt.patient else "—"
        time_str = str(appt.appointment_time)[:5] if appt.appointment_time else "—"
        self._ctx.update(
            patient_name,
            f"{appt.appointment_date}  ·  {time_str}  ·  {appt.status}",
            appt.status,
        )
        if appt.patient:
            self.patient_field.set(f"{appt.patient_id} - {appt.patient.full_name}")
        if appt.doctor:
            self.doctor_field.set(f"{appt.doctor_id} - {appt.doctor.full_name}")
        self.date_field.set(str(appt.appointment_date))
        self.time_field.set(time_str)
        self.reason_field.set(appt.reason or "")
        self.status_field.set(appt.status)

    # ── Save ─────────────────────────────────────────────────────────────────
    def _save(self) -> None:
        try:
            patient_id = int(self.patient_field.get().split(" - ")[0])
        except (ValueError, IndexError):
            show_message(self, "Validation", "Select a valid patient.", "warning")
            return
        appt_date = parse_date(self.date_field.get())
        if not appt_date:
            show_message(self, "Validation", "Invalid date format (use YYYY-MM-DD).", "warning")
            return
        try:
            appt_time = datetime.strptime(self.time_field.get().strip(), "%H:%M").time()
        except ValueError:
            show_message(self, "Validation", "Invalid time format (use HH:MM).", "warning")
            return
        try:
            doctor_id = int(self.doctor_field.get().split(" - ")[0])
        except (ValueError, IndexError):
            doctor_id = None

        data = {
            "patient_id":       patient_id,
            "doctor_id":        doctor_id,
            "appointment_date": appt_date,
            "appointment_time": appt_time,
            "reason":           self.reason_field.get(),
            "status":           self.status_field.get() or "Scheduled",
        }
        if self.selected_id:
            ok, msg = self.appointment_service.update(self.selected_id, data)
        else:
            ok, msg, _ = self.appointment_service.create(data)
        show_message(self, "Appointments", msg, "success" if ok else "error")
        if ok:
            self.refresh()

    # ── Cancel ────────────────────────────────────────────────────────────────
    def _cancel(self) -> None:
        if not self.selected_id:
            show_message(self, "Cancel", "Select an appointment first.", "warning")
            return
        ok, msg = self.appointment_service.cancel(self.selected_id)
        show_message(self, "Appointments", msg, "success" if ok else "error")
        if ok:
            self.refresh()

    # ── Clear ─────────────────────────────────────────────────────────────────
    def _clear(self) -> None:
        self.selected_id = None
        self._ctx.update("No appointment selected",
                         "Select from the schedule or create a new appointment")
        self.date_field.set(str(date.today()))
        self.time_field.set("09:00")
        self.reason_field.set("")
        self.status_field.set("Scheduled")
        for rw in self._row_widgets:
            rw.select(False)
