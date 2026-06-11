"""PDF document generators for receipts, prescriptions, patient profiles, and PhilHealth claim forms."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable


class PDFGenerator:
    @staticmethod
    def generate_receipt(
        output_path: str,
        clinic_name: str,
        clinic_address: str,
        receipt_number: str,
        patient_name: str,
        items: list,
        subtotal: float,
        discount: float,
        philhealth_deduction: float,
        total: float,
        amount_paid: float,
        header: str = "",
        footer: str = "",
    ) -> None:
        doc = SimpleDocTemplate(output_path, pagesize=letter, topMargin=0.5 * inch)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph(clinic_name, styles["Title"]))
        if clinic_address:
            elements.append(Paragraph(clinic_address, styles["Normal"]))
        if header:
            elements.append(Paragraph(header, styles["Normal"]))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"<b>OFFICIAL RECEIPT</b>", styles["Heading2"]))
        elements.append(Paragraph(f"Receipt No: {receipt_number}", styles["Normal"]))
        elements.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y %I:%M %p')}", styles["Normal"]))
        elements.append(Paragraph(f"Patient: {patient_name}", styles["Normal"]))
        elements.append(Spacer(1, 12))

        table_data = [["Description", "Qty", "Price", "Total"]]
        for item in items:
            table_data.append([
                item.get("description", ""),
                str(item.get("quantity", 1)),
                f"₱{item.get('unit_price', 0):,.2f}",
                f"₱{item.get('total_price', 0):,.2f}",
            ])

        table = Table(table_data, colWidths=[3 * inch, 0.7 * inch, 1 * inch, 1 * inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 12))

        summary = [
            ["Subtotal:", f"₱{subtotal:,.2f}"],
            ["Discount:", f"₱{discount:,.2f}"],
            ["PhilHealth Deduction:", f"₱{philhealth_deduction:,.2f}"],
            ["Total:", f"₱{total:,.2f}"],
            ["Amount Paid:", f"₱{amount_paid:,.2f}"],
        ]
        summary_table = Table(summary, colWidths=[2 * inch, 1.5 * inch])
        summary_table.setStyle(TableStyle([
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("FONTNAME", (0, -2), (-1, -1), "Helvetica-Bold"),
        ]))
        elements.append(summary_table)

        if footer:
            elements.append(Spacer(1, 24))
            elements.append(Paragraph(footer, styles["Normal"]))

        doc.build(elements)

    @staticmethod
    def generate_prescription(
        output_path: str,
        clinic_name: str,
        patient_name: str,
        patient_age: str,
        doctor_name: str,
        items: list,
        date_str: Optional[str] = None,
    ) -> None:
        doc = SimpleDocTemplate(output_path, pagesize=letter, topMargin=0.5 * inch)
        styles = getSampleStyleSheet()
        rx_style = ParagraphStyle("Rx", parent=styles["Title"], fontSize=28, textColor=colors.HexColor("#2563EB"))
        elements = []

        elements.append(Paragraph(clinic_name, styles["Title"]))
        elements.append(Paragraph("℞ PRESCRIPTION", rx_style))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Patient: <b>{patient_name}</b>  |  Age: {patient_age}", styles["Normal"]))
        elements.append(Paragraph(f"Date: {date_str or datetime.now().strftime('%B %d, %Y')}", styles["Normal"]))
        elements.append(Spacer(1, 20))

        for i, item in enumerate(items, 1):
            elements.append(Paragraph(
                f"{i}. <b>{item.get('medicine_name', '')}</b> — {item.get('dosage', '')} "
                f"{item.get('frequency', '')} for {item.get('duration', '')}",
                styles["Normal"],
            ))
            if item.get("instructions"):
                elements.append(Paragraph(f"   <i>{item['instructions']}</i>", styles["Normal"]))
            elements.append(Spacer(1, 8))

        elements.append(Spacer(1, 40))
        elements.append(Paragraph(f"Prescribing Physician: <b>{doctor_name}</b>", styles["Normal"]))
        elements.append(Paragraph("_" * 40, styles["Normal"]))

        doc.build(elements)

    @staticmethod
    def generate_philhealth_summary(
        output_path: str,
        clinic_name: str,
        patient_name: str,
        philhealth_number: str,
        case_description: str,
        computation: dict,
    ) -> None:
        doc = SimpleDocTemplate(output_path, pagesize=letter, topMargin=0.5 * inch)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph(clinic_name, styles["Title"]))
        elements.append(Paragraph("<b>PhilHealth Benefit Summary</b>", styles["Heading2"]))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Patient: {patient_name}", styles["Normal"]))
        elements.append(Paragraph(f"PhilHealth No: {philhealth_number}", styles["Normal"]))
        elements.append(Paragraph(f"Case: {case_description}", styles["Normal"]))
        elements.append(Spacer(1, 16))

        rows = [
            ["Case Rate Amount", f"₱{float(computation.get('case_rate_amount', 0)):,.2f}"],
            ["Hospital Share (70%)", f"₱{float(computation.get('hospital_share', 0)):,.2f}"],
            ["Professional Fee (30%)", f"₱{float(computation.get('professional_fee', 0)):,.2f}"],
            ["PhilHealth Deduction", f"₱{float(computation.get('philhealth_deduction', 0)):,.2f}"],
            ["Senior Discount", f"₱{float(computation.get('senior_discount', 0)):,.2f}"],
            ["PWD Discount", f"₱{float(computation.get('pwd_discount', 0)):,.2f}"],
            ["Patient Balance", f"₱{float(computation.get('patient_balance', 0)):,.2f}"],
        ]
        table = Table(rows, colWidths=[3 * inch, 2 * inch])
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#F8F9FA")),
        ]))
        elements.append(table)
        doc.build(elements)

    # ------------------------------------------------------------------ #
    #  PhilHealth Claim Forms  CF1 / CF2 / CF3 / CF4 / CF5 / CSF         #
    # ------------------------------------------------------------------ #

    _PH_PAGE_W = 6.95 * inch
    _PH_FONT = "Helvetica"
    _PH_FONT_BOLD = "Helvetica-Bold"
    _PH_FS = 9
    _PH_FS_SM = 8
    _PH_FS_TITLE = 11
    _PH_BORDER = colors.HexColor("#555555")
    _PH_RULE = colors.HexColor("#BBBBBB")
    _PH_HDR_BG = colors.HexColor("#EDEDED")
    _PH_ROW_ALT = colors.HexColor("#F9F9F9")

    @staticmethod
    def _ph_val(value) -> str:
        if value is None:
            return "N/A"
        s = str(value).strip()
        return s if s and s not in ("—", "-", "None", "none") else "N/A"

    @classmethod
    def _ph_pair_cols(cls) -> list:
        """Label column ~36%, value column ~64% — room for long government labels."""
        w = cls._PH_PAGE_W
        return [w * 0.36, w * 0.64]

    @classmethod
    def _ph_quad_cols(cls) -> list:
        """Four-column layout for short-label rows (dates/times)."""
        w = cls._PH_PAGE_W
        return [w * 0.22, w * 0.28, w * 0.22, w * 0.28]

    @staticmethod
    def _ph_escape(text) -> str:
        s = str(text or "")
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    @classmethod
    def _ph_label_para(cls, text) -> Paragraph:
        return Paragraph(
            f"<b>{cls._ph_escape(text)}</b>",
            ParagraphStyle(
                "ph_lbl", fontName=cls._PH_FONT_BOLD, fontSize=cls._PH_FS,
                leading=12, textColor=colors.black,
            ),
        )

    @classmethod
    def _ph_value_para(cls, text) -> Paragraph:
        return Paragraph(
            cls._ph_escape(cls._ph_val(text)),
            ParagraphStyle(
                "ph_val", fontName=cls._PH_FONT, fontSize=cls._PH_FS,
                leading=12, textColor=colors.black,
            ),
        )

    @classmethod
    def _ph_grid_style(cls) -> list:
        return [
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("BOX", (0, 0), (-1, -1), 0.5, cls._PH_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, cls._PH_RULE),
        ]

    @classmethod
    def _expand_field_rows(cls, rows: list) -> list:
        """Split 4-column rows into 2-column pairs so labels never crowd values."""
        expanded = []
        for row in rows:
            cells = list(row)
            while len(cells) < 4:
                cells.append("")
            if len(cells) == 4:
                if cells[0]:
                    expanded.append([cells[0], cells[1]])
                if cells[2]:
                    expanded.append([cells[2], cells[3]])
            elif len(cells) == 2:
                if cells[0]:
                    expanded.append(cells)
        return expanded

    @classmethod
    def _philhealth_header(cls, elements: list, styles, clinic_name: str,
                           form_label: str, form_number: str) -> None:
        """Clean government-style header — normal Helvetica, no decorative colors."""
        form_lines = [ln.strip() for ln in form_label.split("\n") if ln.strip()]
        form_title = form_lines[0] if form_lines else form_label
        form_sub = "<br/>".join(form_lines[1:]) if len(form_lines) > 1 else ""

        title_style = ParagraphStyle(
            "ph_title", parent=styles["Normal"], fontName=cls._PH_FONT_BOLD,
            fontSize=cls._PH_FS_TITLE, leading=13, textColor=colors.black,
        )
        sub_style = ParagraphStyle(
            "ph_sub", parent=styles["Normal"], fontName=cls._PH_FONT,
            fontSize=cls._PH_FS_SM, leading=11, alignment=2, textColor=colors.black,
        )
        body_style = ParagraphStyle(
            "ph_body", parent=styles["Normal"], fontName=cls._PH_FONT,
            fontSize=cls._PH_FS, leading=12, textColor=colors.black,
        )

        half = cls._PH_PAGE_W / 2
        header_data = [[
            Paragraph("PHILHEALTH", title_style),
            Paragraph(
                form_title + (f"<br/>{form_sub}" if form_sub else ""),
                sub_style,
            ),
        ]]
        header_table = Table(header_data, colWidths=[half, half])
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(header_table)
        elements.append(HRFlowable(width="100%", thickness=1, color=cls._PH_BORDER))
        elements.append(Spacer(1, 6))

        cls._field_table(elements, [
            ["Facility Name", clinic_name, "Form No.", form_number],
            ["Date Printed", datetime.now().strftime("%B %d, %Y"), "", ""],
        ])
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(
            "IMPORTANT: All information must be true and correct. "
            "False statements are subject to applicable penalties under the law.",
            ParagraphStyle("ph_note", parent=body_style, fontSize=cls._PH_FS_SM,
                           textColor=colors.HexColor("#333333")),
        ))
        elements.append(Spacer(1, 8))

    @classmethod
    def _section_title(cls, elements: list, styles, title: str) -> None:
        bar = Table([[title]], colWidths=[cls._PH_PAGE_W])
        bar.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), cls._PH_FONT_BOLD),
            ("FONTSIZE", (0, 0), (-1, -1), cls._PH_FS),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
            ("BACKGROUND", (0, 0), (-1, -1), cls._PH_HDR_BG),
            ("BOX", (0, 0), (-1, -1), 0.5, cls._PH_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(Spacer(1, 10))
        elements.append(bar)
        elements.append(Spacer(1, 4))

    @classmethod
    def _field_table(cls, elements: list, rows: list, col_widths=None) -> None:
        col_widths = col_widths or cls._ph_pair_cols()
        table_data = [
            [cls._ph_label_para(label), cls._ph_value_para(value)]
            for label, value in cls._expand_field_rows(rows)
        ]
        if not table_data:
            return
        t = Table(table_data, colWidths=col_widths)
        t.setStyle(TableStyle(cls._ph_grid_style()))
        elements.append(t)
        elements.append(Spacer(1, 4))

    @classmethod
    def _confinement_table(cls, elements: list, admission_date, discharge_date,
                           time_admitted, time_discharged, type_of_admission,
                           patient_disposition) -> None:
        rows = [
            [
                cls._ph_label_para("Date Admitted"),
                cls._ph_value_para(admission_date),
                cls._ph_label_para("Time Admitted"),
                cls._ph_value_para(time_admitted),
            ],
            [
                cls._ph_label_para("Date Discharged"),
                cls._ph_value_para(discharge_date),
                cls._ph_label_para("Time Discharged"),
                cls._ph_value_para(time_discharged),
            ],
            [
                cls._ph_label_para("Type of Admission"),
                cls._ph_value_para(type_of_admission),
                cls._ph_label_para("Patient Disposition"),
                cls._ph_value_para(patient_disposition),
            ],
        ]
        t = Table(rows, colWidths=cls._ph_quad_cols())
        t.setStyle(TableStyle(cls._ph_grid_style()))
        elements.append(t)
        elements.append(Spacer(1, 4))

    @classmethod
    def _charges_table(cls, elements: list, charges: list) -> None:
        w = cls._PH_PAGE_W
        t = Table(charges, colWidths=[w * 0.72, w * 0.28])
        style_cmds = [
            ("FONTNAME", (0, 0), (-1, -1), cls._PH_FONT),
            ("FONTSIZE", (0, 0), (-1, -1), cls._PH_FS),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
            ("BOX", (0, 0), (-1, -1), 0.5, cls._PH_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, cls._PH_RULE),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("FONTNAME", (0, 0), (-1, 0), cls._PH_FONT_BOLD),
            ("BACKGROUND", (0, 0), (-1, 0), cls._PH_HDR_BG),
        ]
        for i in range(1, len(charges)):
            if i % 2 == 0:
                style_cmds.append(("BACKGROUND", (0, i), (-1, i), cls._PH_ROW_ALT))
            label = str(charges[i][0]).lower()
            if "sub-total" in label or "total amount" in label:
                style_cmds.append(("FONTNAME", (0, i), (-1, i), cls._PH_FONT_BOLD))
                style_cmds.append(("LINEABOVE", (0, i), (-1, i), 0.75, cls._PH_BORDER))
        t.setStyle(TableStyle(style_cmds))
        elements.append(t)

    @classmethod
    def _cert_block(cls, elements: list, title: str, left_text: str, right_text: str) -> None:
        rows = [[title, ""], [left_text, right_text]]
        half = cls._PH_PAGE_W / 2
        t = Table(rows, colWidths=[half, half])
        t.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), cls._PH_FONT),
            ("FONTSIZE", (0, 0), (-1, -1), cls._PH_FS_SM),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
            ("SPAN", (0, 0), (-1, 0)),
            ("FONTNAME", (0, 0), (-1, 0), cls._PH_FONT_BOLD),
            ("FONTSIZE", (0, 0), (-1, 0), cls._PH_FS),
            ("BACKGROUND", (0, 0), (-1, 0), cls._PH_HDR_BG),
            ("BOX", (0, 0), (-1, -1), 0.5, cls._PH_BORDER),
            ("LINEAFTER", (0, 1), (0, 1), 0.5, cls._PH_RULE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(Spacer(1, 12))
        elements.append(t)

    @classmethod
    def _signature_block(cls, elements: list, styles) -> None:
        cls._cert_block(
            elements,
            "CERTIFICATION",
            "Signature over Printed Name\n\n\n_______________________________",
            "Date\n\n\n_______________________________",
        )

    @classmethod
    def _ph_doc_title(cls, patient_name: str, form_type: str) -> str:
        name = (patient_name or "").strip()
        if not name or name in ("—", "-", "N/A"):
            name = "Patient"
        ft = (form_type or "Claim Form").strip()
        return f"{name} - {ft}"

    @classmethod
    def _ph_doc(cls, output_path: str, patient_name: str, form_type: str,
                clinic_name: str = "") -> SimpleDocTemplate:
        return SimpleDocTemplate(
            output_path,
            pagesize=A4,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
            leftMargin=0.65 * inch,
            rightMargin=0.65 * inch,
            title=cls._ph_doc_title(patient_name, form_type),
            author=clinic_name or "Hospital Management System",
            subject=f"PhilHealth {form_type} Claim Form",
        )

    @classmethod
    def generate_cf2_cf4(
        cls,
        output_path: str,
        clinic_name: str,
        clinic_address: str,
        accreditation_no: str,
        form_number: str,
        patient_name: str,
        philhealth_number: str,
        member_type: str,
        form_type: str,
        admission_date: str,
        discharge_date: str,
        time_admitted: str = "—",
        time_discharged: str = "—",
        type_of_admission: str = "Ordinary",
        patient_disposition: str = "Improved",
        accommodation_type: str = "Non-Private",
        admission_diagnosis: str = "—",
        referring_hci: str = "—",
        attending_physician: str = "—",
        diagnosis: str = "—",
        icd_code: str = "—",
        case_rate_code: str = "—",
        second_case_rate_code: str = "—",
        room_charges: float = 0,
        medicine_charges: float = 0,
        xray_lab_charges: float = 0,
        other_charges: float = 0,
        hospital_share: float = 0,
        total_claimed: float = 0,
        date_of_claim: str = "",
        notes: str = "",
    ) -> None:
        """Unified generator for CF2 (Hospital) and CF4 (Outpatient)."""
        is_cf2 = (form_type == "CF2")
        form_title = (
            "CLAIM FORM 2 (CF2)\nHospital / Facility Claim Form\nRevised September 2018"
            if is_cf2 else
            "CLAIM FORM 4 (CF4)\nAll Case Rates / Outpatient Claim Form\nFebruary 2020"
        )
        doc = cls._ph_doc(output_path, patient_name, form_type, clinic_name)
        styles = getSampleStyleSheet()
        E = []

        cls._philhealth_header(E, styles, clinic_name, form_title, form_number)

        # ── Part I: HCI ───────────────────────────────────────────────────────
        cls._section_title(E, styles, "PART I – HEALTH CARE INSTITUTION (HCI) INFORMATION")
        cls._field_table(E, [
            ["PhilHealth Accreditation No. (PAN)", accreditation_no,
             "Name of Health Care Institution", clinic_name],
            ["Address", clinic_address, "", ""],
        ])

        # ── Part II: Patient ──────────────────────────────────────────────────
        cls._section_title(E, styles, "PART II – PATIENT CONFINEMENT INFORMATION")
        cls._field_table(E, [
            ["Patient Name", patient_name,
             "PhilHealth Identification No. (PIN)", philhealth_number],
            ["Member Type", member_type,
             "Accommodation Type", accommodation_type],
            ["Referred from another HCI", referring_hci or "No",
             "Attending Physician", attending_physician],
        ])
        cls._confinement_table(
            E, admission_date, discharge_date, time_admitted, time_discharged,
            type_of_admission, patient_disposition,
        )

        # ── Diagnoses ─────────────────────────────────────────────────────────
        cls._section_title(E, styles, "ADMISSION & DISCHARGE DIAGNOSES")
        cls._field_table(E, [
            ["Admission Diagnosis", admission_diagnosis, "ICD-10 Code", icd_code],
            ["Discharge Diagnosis", diagnosis, "", ""],
        ])

        # ── PhilHealth Benefits ───────────────────────────────────────────────
        cls._section_title(E, styles, "PHILHEALTH BENEFITS")
        cr2_display = second_case_rate_code if second_case_rate_code not in ("—", "", None) else "N/A"
        cls._field_table(E, [
            ["ICD-10 / RVS Code", icd_code,
             "1st Case Rate Code", case_rate_code],
            ["2nd Case Rate Code", cr2_display, "", ""],
        ])

        # ── Charges ───────────────────────────────────────────────────────────
        cls._section_title(E, styles,
            "PART III – CHARGES / CONSUMPTION OF BENEFITS" if is_cf2
            else "CHARGES & PHILHEALTH BENEFIT")

        room_label   = "Room & Board Charges" if is_cf2 else "Consultation / Prof. Fee"
        lab_label    = "X-Ray / Laboratory Charges" if is_cf2 else "Laboratory / Diagnostics"
        hsp_label    = "Hospital Share (PhilHealth)" if is_cf2 else "PhilHealth Benefit"
        subtotal     = room_charges + medicine_charges + xray_lab_charges + other_charges
        patient_pays = max(0.0, subtotal - hospital_share)

        charges = [
            ["Description", "Amount (PHP)"],
            [room_label,               f"{room_charges:,.2f}"],
            ["Medicine and Drug Charges", f"{medicine_charges:,.2f}"],
            [lab_label,                f"{xray_lab_charges:,.2f}"],
            ["Other Charges",          f"{other_charges:,.2f}"],
            ["Sub-Total",              f"{subtotal:,.2f}"],
            [hsp_label,               f"({hospital_share:,.2f})"],
            ["Total Amount Claimed",   f"{total_claimed:,.2f}"],
            ["Patient Co-Pay / Balance", f"{patient_pays:,.2f}"],
        ]
        cls._charges_table(E, charges)

        # ── Signatures ────────────────────────────────────────────────────────
        cls._cert_block(
            E,
            "PART IV – CERTIFICATION",
            "I certify that the services rendered are true and correct.\n\n\n"
            "_________________________________________\n"
            "Signature over Printed Name of Authorized HCI Representative\n"
            "Date Signed: ___________________________",
            "Member / Patient Consent\n"
            "I hereby consent to the submission of patient records.\n\n\n"
            "_________________________________________\n"
            "Signature over Printed Name of Member / Patient\n"
            "Date Signed: ___________________________",
        )

        if notes and notes not in ("—", ""):
            cls._section_title(E, styles, "REMARKS / NOTES")
            clean = notes[:500] if len(notes) > 500 else notes
            E.append(Paragraph(clean, ParagraphStyle(
                "note2", parent=styles["Normal"], fontName=cls._PH_FONT,
                fontSize=cls._PH_FS_SM, textColor=colors.black)))

        doc.build(E)

    @classmethod
    def generate_cf3(
        cls,
        output_path: str,
        clinic_name: str,
        clinic_address: str = "",
        accreditation_no: str = "",
        form_number: str = "",
        patient_name: str = "",
        philhealth_number: str = "",
        member_type: str = "",
        diagnosis: str = "",
        icd_code: str = "",
        case_rate_code: str = "",
        second_case_rate_code: str = "",
        total_claimed: float = 0,
        date_of_claim: str = "",
        admission_date: str = "",
        discharge_date: str = "",
        time_admitted: str = "",
        time_discharged: str = "",
        patient_disposition: str = "",
        attending_physician: str = "",
        physician_prc_no: str = "",
        physician_ptr_no: str = "",
        physician_philhealth_no: str = "",
        notes: str = "",
        **_,
    ) -> None:
        """Generate PhilHealth CF3 – Clinical Record."""
        doc = cls._ph_doc(output_path, patient_name, "CF3", clinic_name)
        styles = getSampleStyleSheet()
        E = []

        cls._philhealth_header(E, styles, clinic_name,
                               "CLAIM FORM 3 (CF3)\nClinical Record\nRevised November 2013",
                               form_number)

        cls._section_title(E, styles, "PART I – PATIENT'S CLINICAL RECORD")
        cls._field_table(E, [
            ["PhilHealth Accreditation No. (PAN)", accreditation_no,
             "Patient Name", patient_name],
            ["PhilHealth No. (PIN)", philhealth_number,
             "Member Type", member_type],
            ["Date Admitted", admission_date, "Time Admitted", time_admitted],
            ["Date Discharged", discharge_date, "Time Discharged", time_discharged],
            ["Disposition on Discharge", patient_disposition, "", ""],
        ])

        cls._section_title(E, styles, "DIAGNOSIS & CASE RATE")
        cls._field_table(E, [
            ["Discharge Diagnosis", diagnosis, "ICD-10 Code", icd_code],
            ["Case Rate Code", case_rate_code,
             "Total Amount Claimed", f"PHP {total_claimed:,.2f}"],
        ])

        cls._section_title(E, styles, "ATTENDING PHYSICIAN / MIDWIFE CERTIFICATION")
        cls._field_table(E, [
            ["Physician Name", attending_physician, "PRC No.", physician_prc_no],
            ["PTR No.", physician_ptr_no, "PhilHealth No.", physician_philhealth_no],
        ])

        cls._section_title(E, styles, "CLINICAL NOTES")
        note_style = ParagraphStyle(
            "cn", parent=styles["Normal"], fontName=cls._PH_FONT,
            fontSize=cls._PH_FS_SM, textColor=colors.black,
            borderPad=6, borderColor=cls._PH_RULE,
            borderWidth=0.5, backColor=colors.white,
        )

        def _extract(tag, text):
            import re
            m = re.search(rf"{tag}:([^A-Z_]{{0,500}}?)(?:[A-Z_]{{3,}}:|$)", text, re.DOTALL)
            return m.group(1).strip()[:300] if m else ""

        lines = []
        for tag, label in [("CHIEF", "Chief Complaint"), ("GENL", "General Survey"),
                           ("HEENT", "HEENT"), ("CHEST", "Chest/Lungs"),
                           ("LABS", "Lab Findings"), ("COURSE", "Course in Ward")]:
            val = _extract(tag, notes)
            if val and val not in ("—", ""):
                lines.append(f"<b>{label}:</b>  {val}")
        body_text = "<br/><br/>".join(lines) if lines else (notes[:600] if notes else "N/A")
        E.append(Paragraph(body_text, note_style))

        cls._cert_block(
            E,
            "CERTIFICATION OF ATTENDING PHYSICIAN / MIDWIFE",
            "I certify that the above information is true and correct.\n\n\n"
            "_________________________________________\n"
            "Signature over Printed Name of Attending Physician / Midwife",
            f"Date Signed: {cls._ph_val(date_of_claim)}\n\n\n"
            "_________________________________________\n"
            "Official Stamp (if applicable)",
        )
        doc.build(E)

    @classmethod
    def generate_cf5(
        cls,
        output_path: str,
        clinic_name: str,
        clinic_address: str = "",
        accreditation_no: str = "",
        form_number: str = "",
        patient_name: str = "",
        philhealth_number: str = "",
        member_type: str = "",
        dialysis_center_name: str = "",
        dialysis_center_accreditation: str = "",
        dialysis_type: str = "Hemodialysis",
        period_from: str = "",
        period_to: str = "",
        number_of_sessions: int = 0,
        total_claimed: float = 0,
        diagnosis: str = "",
        icd_code: str = "",
        case_rate_code: str = "",
        date_of_claim: str = "",
        notes: str = "",
        **_,
    ) -> None:
        """Generate PhilHealth CF5 – ESRD / Dialysis Claim Form."""
        doc = cls._ph_doc(output_path, patient_name, "CF5", clinic_name)
        styles = getSampleStyleSheet()
        E = []

        cls._philhealth_header(E, styles, clinic_name,
                               "CLAIM FORM 5 (CF5)\nEnd-Stage Renal Disease (ESRD) / Dialysis Claim",
                               form_number)

        cls._section_title(E, styles, "PATIENT / MEMBER INFORMATION")
        cls._field_table(E, [
            ["Patient Name", patient_name, "PhilHealth No. (PIN)", philhealth_number],
            ["Member Type", member_type, "Diagnosis", diagnosis],
            ["ICD-10 Code", icd_code, "Case Rate Code", case_rate_code],
        ])

        cls._section_title(E, styles, "DIALYSIS CENTER INFORMATION")
        cls._field_table(E, [
            ["Center Name", dialysis_center_name,
             "Accreditation No.", dialysis_center_accreditation],
            ["Dialysis Type", dialysis_type, "", ""],
        ])

        cls._section_title(E, styles, "TREATMENT PERIOD & CLAIM SUMMARY")
        per_session = (total_claimed / number_of_sessions) if number_of_sessions else 0
        summary = [
            ["Description", "Amount (PHP)"],
            ["Period From", period_from],
            ["Period To", period_to],
            ["Number of Sessions", str(number_of_sessions or 0)],
            ["Rate per Session", f"{per_session:,.2f}"],
            ["Total Amount Claimed", f"{total_claimed:,.2f}"],
        ]
        cls._charges_table(E, summary)

        cls._signature_block(E, styles)
        if notes:
            cls._section_title(E, styles, "REMARKS / NOTES")
            E.append(Paragraph(notes[:400], ParagraphStyle(
                "n", parent=styles["Normal"], fontName=cls._PH_FONT,
                fontSize=cls._PH_FS_SM, textColor=colors.black)))
        doc.build(E)

    @classmethod
    def generate_cf1_csf(
        cls,
        output_path: str,
        clinic_name: str,
        form_number: str,
        patient_name: str,
        philhealth_number: str,
        form_type: str = "CF1",
        admission_date: str = "",
        discharge_date: str = "",
        diagnosis: str = "",
        icd_code: str = "",
        case_rate_code: str = "",
        second_case_rate_code: str = "",
        total_claimed: float = 0,
        date_of_claim: str = "",
        notes: str = "",
        clinic_address: str = "",
        accreditation_no: str = "",
        member_type: str = "",
        **_,
    ) -> None:
        """Generate CF1 (Member Info) or CSF (Claim Signature Form)."""
        is_csf = (form_type == "CSF")
        title = (
            "CLAIM SIGNATURE FORM (CSF)\nRevised September 2018"
            if is_csf else
            "CLAIM FORM 1 (CF1)\nMember Information Form\nRevised September 2018"
        )
        doc = cls._ph_doc(output_path, patient_name, form_type, clinic_name)
        styles = getSampleStyleSheet()
        E = []
        cls._philhealth_header(E, styles, clinic_name, title, form_number)

        # Parse notes for extra fields
        import re
        def _ex(tag, text):
            m = re.search(rf"{tag}:([^A-Z_]{{0,300}}?)(?=[A-Z_]{{3,}}:|$)", text)
            return m.group(1).strip() if m else "—"

        dob     = _ex("DOB",    notes)
        sex     = _ex("SEX",    notes)
        rel     = _ex("REL",    notes)
        emp_nm  = _ex("EMPNM",  notes)
        pen     = _ex("PEN",    notes)
        hcp1    = _ex("HCP1",   notes)
        hcp2    = _ex("HCP2",   notes)
        hcp3    = _ex("HCP3",   notes)
        pan     = _ex("PAN",    notes) or accreditation_no
        hci_n   = _ex("HCI",    notes) or clinic_name

        cls._section_title(E, styles, "PART I – MEMBER AND PATIENT INFORMATION")
        cls._field_table(E, [
            ["Patient / Member Name", patient_name,
             "PhilHealth Identification No. (PIN)", philhealth_number],
            ["Date of Birth", dob, "Sex", sex],
            ["Relationship to Member", rel, "", ""],
            ["Date Admitted", admission_date, "Date Discharged", discharge_date],
        ])

        if is_csf:
            cls._section_title(E, styles, "PHILHEALTH BENEFITS (PART V)")
            cr2 = second_case_rate_code or "N/A"
            cls._field_table(E, [
                ["Diagnosis", diagnosis, "ICD-10 / RVS Code", icd_code],
                ["1st Case Rate Code", case_rate_code, "2nd Case Rate Code", cr2],
                ["Total Amount Claimed", f"PHP {total_claimed:,.2f}", "", ""],
            ])

        cls._section_title(E, styles, "PART II – EMPLOYER'S CERTIFICATION (employed members only)")
        cls._field_table(E, [
            ["PhilHealth Employer No. (PEN)", pen,
             "Business Name", emp_nm],
        ])

        if is_csf:
            cls._section_title(E, styles, "PART IV – HEALTH CARE PROFESSIONAL INFORMATION")
            cls._field_table(E, [
                ["HCP 1 – Accreditation No.", hcp1, "", ""],
                ["HCP 2 – Accreditation No.", hcp2, "", ""],
                ["HCP 3 – Accreditation No.", hcp3, "", ""],
            ])

        cls._cert_block(
            E,
            "MEMBER / PATIENT CERTIFICATION",
            "Under penalty of law, I attest that the information provided in this form "
            "is true and accurate.\n\n\n"
            "_________________________________________\n"
            "Signature of Member / Patient\n"
            "Date Signed: ___________________________",
            f"HCI Name: {cls._ph_val(hci_n)}\n"
            f"PAN: {cls._ph_val(pan)}\n\n\n"
            "_________________________________________\n"
            "Signature of Authorized HCI Representative\n"
            "Date Signed: ___________________________",
        )
        doc.build(E)

    # ------------------------------------------------------------------ #
    #  Statement of Account (SOA)                                          #
    # ------------------------------------------------------------------ #

    @classmethod
    def generate_soa(
        cls,
        output_path: str,
        clinic_name: str,
        clinic_address: str,
        soa_number: str,
        billing_number: str,
        patient_name: str,
        philhealth_number: str,
        admission_date: str,
        discharge_date: str,
        items: list,
        subtotal: float,
        discount_amount: float,
        discount_type: str,
        philhealth_deduction: float,
        total_amount: float,
        amount_paid: float,
        balance: float,
        case_code: str = "",
        case_description: str = "",
        case_type: str = "",
        case_rate: float = 0,
        health_facility_fee: float = 0,
        professional_fee_ph: float = 0,
        ph_effective_date=None,
        header: str = "",
        footer: str = "",
    ) -> None:
        """Generate a printable Statement of Account (SOA) PDF."""
        doc = SimpleDocTemplate(
            output_path, pagesize=A4,
            topMargin=0.5 * inch, bottomMargin=0.6 * inch,
            leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        )
        styles = getSampleStyleSheet()
        ph_blue  = colors.HexColor("#0057A8")
        ph_green = colors.HexColor("#007749")
        red      = colors.HexColor("#DC2626")
        gray     = colors.HexColor("#F1F5F9")
        elements = []

        title_style = ParagraphStyle("soatitle2", parent=styles["Title"], fontSize=15,
                                     textColor=ph_blue, spaceAfter=2)
        sub_style   = ParagraphStyle("soasub", parent=styles["Normal"], fontSize=9,
                                     textColor=colors.HexColor("#475569"))
        elements.append(Paragraph(clinic_name, title_style))
        if clinic_address:
            elements.append(Paragraph(clinic_address, sub_style))
        if header:
            elements.append(Paragraph(header, sub_style))
        elements.append(HRFlowable(width="100%", thickness=2, color=ph_blue))
        elements.append(Spacer(1, 6))

        soa_hdr = Table(
            [[
                Paragraph("<b>STATEMENT OF ACCOUNT</b>",
                          ParagraphStyle("soahdr", parent=styles["Heading2"],
                                         textColor=ph_blue, fontSize=13)),
                Paragraph(
                    f"SOA No: <b>{soa_number}</b><br/>Billing No: {billing_number}<br/>"
                    f"Date: {datetime.now().strftime('%B %d, %Y')}",
                    ParagraphStyle("soa_r2", parent=styles["Normal"], fontSize=9, alignment=2)),
            ]],
            colWidths=[4 * inch, 3 * inch],
        )
        soa_hdr.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        elements.append(soa_hdr)
        elements.append(Spacer(1, 6))

        cls._section_title(elements, styles, "PATIENT INFORMATION")
        cls._field_table(elements, [
            ["Patient Name:", patient_name, "PhilHealth No:", philhealth_number or "—"],
            ["Admission Date:", admission_date or "—", "Discharge Date:", discharge_date or "—"],
        ])

        cls._section_title(elements, styles, "ITEMIZED CHARGES")
        charges_data = [["Description", "Type", "Qty", "Unit Price (₱)", "As of", "Total (₱)"]]
        for item in items:
            as_of = item.get("price_as_of")
            as_of_str = as_of.strftime("%b %d, %Y") if hasattr(as_of, "strftime") else str(as_of or "—")
            charges_data.append([
                item.get("description", ""),
                item.get("item_type", ""),
                str(item.get("quantity", 1)),
                f"{float(item.get('unit_price', 0)):,.2f}",
                as_of_str,
                f"{float(item.get('total_price', 0)):,.2f}",
            ])
        charges_data.append(["", "", "", "", "SUBTOTAL", f"{subtotal:,.2f}"])

        ct = Table(
            charges_data,
            colWidths=[2.2 * inch, 0.85 * inch, 0.35 * inch, 0.85 * inch, 0.75 * inch, 0.85 * inch],
            repeatRows=1,
        )
        ct.setStyle(TableStyle([
            ("BACKGROUND",     (0, 0), (-1, 0), ph_blue),
            ("TEXTCOLOR",      (0, 0), (-1, 0), colors.white),
            ("FONTNAME",       (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME",       (4, -1), (-1, -1), "Helvetica-Bold"),
            ("BACKGROUND",     (0, -1), (-1, -1), gray),
            ("GRID",           (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("ALIGN",          (2, 0), (-1, -1), "RIGHT"),
            ("FONTSIZE",       (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#F8FAFC")]),
        ]))
        elements.append(ct)
        elements.append(Spacer(1, 8))

        if case_code:
            cls._section_title(elements, styles, "PHILHEALTH COVERAGE")
            ph_label = "Medical Case Rate (ICD-10)" if case_type == "Medical" \
                else "Surgical Procedure Case Rate (RVS)"
            as_of_ph = ""
            if ph_effective_date:
                d = ph_effective_date.strftime("%B %d, %Y") if hasattr(ph_effective_date, "strftime") else str(ph_effective_date)
                as_of_ph = f"Price as of: {d}"
            cls._field_table(elements, [
                ["Coverage Type:", ph_label, "Case Code:", case_code],
                ["Description:", case_description[:55], "Rate as of:", as_of_ph or "—"],
            ])
            cov_rows = [
                ["Description", "Amount (₱)"],
                [f"PhilHealth Case Rate ({case_type})", f"{case_rate:,.2f}"],
                ["  Hospital / Facility Share", f"{health_facility_fee:,.2f}"],
                ["  Professional Fee Share", f"{professional_fee_ph:,.2f}"],
                ["PhilHealth Deduction Applied", f"({philhealth_deduction:,.2f})"],
            ]
            cov_t = Table(cov_rows, colWidths=[4.5 * inch, 2 * inch])
            cov_t.setStyle(TableStyle([
                ("BACKGROUND",     (0, 0), (-1, 0), ph_green),
                ("TEXTCOLOR",      (0, 0), (-1, 0), colors.white),
                ("FONTNAME",       (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME",       (0, -1), (-1, -1), "Helvetica-Bold"),
                ("TEXTCOLOR",      (0, -1), (-1, -1), ph_green),
                ("GRID",           (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("ALIGN",          (1, 0), (1, -1), "RIGHT"),
                ("FONTSIZE",       (0, 0), (-1, -1), 9),
                ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#F0FDF4")]),
            ]))
            elements.append(cov_t)
            elements.append(Spacer(1, 8))

        cls._section_title(elements, styles, "BILLING SUMMARY")
        summary_rows = [["Description", "Amount (₱)"]]
        summary_rows.append(["Subtotal", f"{subtotal:,.2f}"])
        if discount_amount > 0:
            summary_rows.append([f"Discount ({discount_type or ''})", f"({discount_amount:,.2f})"])
        if philhealth_deduction > 0:
            summary_rows.append(["PhilHealth Deduction", f"({philhealth_deduction:,.2f})"])
        summary_rows.append(["NET AMOUNT DUE", f"{total_amount:,.2f}"])
        summary_rows.append(["Amount Paid", f"{amount_paid:,.2f}"])
        summary_rows.append(["REMAINING BALANCE", f"{balance:,.2f}"])

        st_sum = Table(summary_rows, colWidths=[4.5 * inch, 2 * inch])
        st_sum.setStyle(TableStyle([
            ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("FONTNAME",   (0, -3), (-1, -3), "Helvetica-Bold"),
            ("FONTNAME",   (0, -1), (-1, -1), "Helvetica-Bold"),
            ("BACKGROUND", (0, -3), (-1, -3), colors.HexColor("#EAF4FF")),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#FEF2F2")),
            ("TEXTCOLOR",  (0, -1), (-1, -1), red),
            ("ALIGN",      (1, 0), (1, -1), "RIGHT"),
            ("FONTSIZE",   (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -4), [colors.white, gray]),
        ]))
        elements.append(st_sum)

        note_style = ParagraphStyle("soanote", parent=styles["Normal"], fontSize=8,
                                    textColor=colors.HexColor("#64748B"), spaceBefore=6)
        elements.append(Paragraph(
            "<i>Prices shown reflect the rates effective at the time each charge was encoded. "
            "Future price changes will not alter this bill.</i>",
            note_style,
        ))

        if footer:
            elements.append(Spacer(1, 20))
            elements.append(Paragraph(footer, sub_style))

        cls._signature_block(elements, styles)
        doc.build(elements)

    # ------------------------------------------------------------------ #
    #  Income Report (Daily / Monthly / Yearly)                           #
    # ------------------------------------------------------------------ #

    @staticmethod
    def generate_income_report(
        output_path: str,
        clinic_name: str,
        report_title: str,
        period_label: str,
        rows: list,
        summary: dict,
    ) -> None:
        """Generate a daily / monthly / yearly income report PDF."""
        doc = SimpleDocTemplate(
            output_path, pagesize=A4,
            topMargin=0.5 * inch, bottomMargin=0.5 * inch,
            leftMargin=0.6 * inch, rightMargin=0.6 * inch,
        )
        styles = getSampleStyleSheet()
        ph_blue = colors.HexColor("#2563EB")
        gray    = colors.HexColor("#F1F5F9")
        elements = []

        elements.append(Paragraph(clinic_name, styles["Title"]))
        elements.append(Paragraph(f"<b>{report_title}</b>",
                                  ParagraphStyle("incrt", parent=styles["Heading2"],
                                                 textColor=ph_blue)))
        elements.append(Paragraph(
            f"Period: {period_label}   |   Generated: "
            f"{datetime.now().strftime('%B %d, %Y %I:%M %p')}",
            styles["Normal"],
        ))
        elements.append(HRFlowable(width="100%", thickness=1, color=ph_blue))
        elements.append(Spacer(1, 10))

        summary_data = [
            ["Total Billings", "Total Collected", "Outstanding Balance", "No. of Bills"],
            [
                f"₱{float(summary.get('total_billed', 0)):,.2f}",
                f"₱{float(summary.get('total_collected', 0)):,.2f}",
                f"₱{float(summary.get('total_balance', 0)):,.2f}",
                str(summary.get("count", 0)),
            ],
        ]
        st = Table(summary_data, colWidths=[1.8 * inch] * 4)
        st.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (-1, 0), ph_blue),
            ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
            ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BACKGROUND",  (0, 1), (-1, 1), colors.HexColor("#EFF6FF")),
            ("FONTNAME",    (0, 1), (-1, 1), "Helvetica-Bold"),
            ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
            ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("FONTSIZE",    (0, 0), (-1, -1), 9),
        ]))
        elements.append(st)
        elements.append(Spacer(1, 12))

        headers = ["Date", "Bill No.", "Patient", "Total (₱)", "Paid (₱)", "Balance (₱)", "Status"]
        detail = [headers]
        for r in rows:
            detail.append([
                r.get("date", ""),
                r.get("billing_no", ""),
                r.get("patient", "")[:28],
                f"{float(r.get('total', 0)):,.2f}",
                f"{float(r.get('paid', 0)):,.2f}",
                f"{float(r.get('balance', 0)):,.2f}",
                r.get("status", ""),
            ])

        cw = [0.85 * inch, 1 * inch, 1.85 * inch, 0.95 * inch, 0.95 * inch, 0.95 * inch, 0.7 * inch]
        dt = Table(detail, colWidths=cw, repeatRows=1)
        dt.setStyle(TableStyle([
            ("BACKGROUND",     (0, 0), (-1, 0), ph_blue),
            ("TEXTCOLOR",      (0, 0), (-1, 0), colors.white),
            ("FONTNAME",       (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID",           (0, 0), (-1, -1), 0.4, colors.HexColor("#E2E8F0")),
            ("ALIGN",          (3, 0), (5, -1), "RIGHT"),
            ("FONTSIZE",       (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, gray]),
        ]))
        elements.append(dt)
        doc.build(elements)
