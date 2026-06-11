"""PDF document generators for receipts, prescriptions, patient profiles, and PhilHealth claim forms."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import Image, SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

from utils.report_icons import ensure_report_icon_path


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
    def _soa_line_items_table(cls, elements: list, items: list, subtotal: float) -> None:
        """Itemized charge grid — same border/typography as CF2 charge tables."""
        w = cls._PH_PAGE_W
        col_widths = [w * 0.32, w * 0.14, w * 0.07, w * 0.13, w * 0.14, w * 0.20]
        rows = [["Description", "Type", "Qty", "Unit Price (PHP)", "As of", "Total (PHP)"]]
        for item in items:
            as_of = item.get("price_as_of")
            if hasattr(as_of, "strftime"):
                as_of_str = as_of.strftime("%b %d, %Y")
            else:
                as_of_str = cls._ph_val(as_of)
            rows.append([
                item.get("description", ""),
                item.get("item_type", ""),
                str(item.get("quantity", 1)),
                f"{float(item.get('unit_price', 0)):,.2f}",
                as_of_str,
                f"{float(item.get('total_price', 0)):,.2f}",
            ])
        rows.append(["", "", "", "", "Sub-Total", f"{subtotal:,.2f}"])

        t = Table(rows, colWidths=col_widths, repeatRows=1)
        style_cmds = [
            ("FONTNAME", (0, 0), (-1, -1), cls._PH_FONT),
            ("FONTSIZE", (0, 0), (-1, -1), cls._PH_FS_SM),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
            ("BOX", (0, 0), (-1, -1), 0.5, cls._PH_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, cls._PH_RULE),
            ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("FONTNAME", (0, 0), (-1, 0), cls._PH_FONT_BOLD),
            ("BACKGROUND", (0, 0), (-1, 0), cls._PH_HDR_BG),
            ("FONTNAME", (0, -1), (-1, -1), cls._PH_FONT_BOLD),
            ("LINEABOVE", (0, -1), (-1, -1), 0.75, cls._PH_BORDER),
        ]
        for i in range(1, len(rows) - 1):
            if i % 2 == 0:
                style_cmds.append(("BACKGROUND", (0, i), (-1, i), cls._PH_ROW_ALT))
        t.setStyle(TableStyle(style_cmds))
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
        accreditation_no: str = "",
        member_type: str = "",
    ) -> None:
        """Generate SOA PDF using the same government-style layout as CF2."""
        doc = cls._ph_doc(output_path, patient_name, "SOA", clinic_name)
        styles = getSampleStyleSheet()
        E = []

        form_label = (
            "STATEMENT OF ACCOUNT (SOA)\n"
            "Hospital / Facility Billing Summary\n"
            "PhilHealth eClaims Supporting Document"
        )
        cls._philhealth_header(E, styles, clinic_name, form_label, soa_number or billing_number)

        cls._section_title(E, styles, "PART I – HEALTH CARE INSTITUTION (HCI) INFORMATION")
        cls._field_table(E, [
            ["PhilHealth Accreditation No. (PAN)", accreditation_no,
             "Name of Health Care Institution", clinic_name],
            ["Address", clinic_address, "Billing Reference No.", billing_number],
        ])
        if header:
            cls._field_table(E, [["Facility Remarks", header, "", ""]])

        cls._section_title(E, styles, "PART II – PATIENT CONFINEMENT INFORMATION")
        cls._field_table(E, [
            ["Patient Name", patient_name,
             "PhilHealth Identification No. (PIN)", philhealth_number],
            ["Member Type", member_type or "N/A",
             "SOA Reference No.", soa_number or billing_number],
        ])
        cls._confinement_table(
            E, admission_date, discharge_date, "—", "—",
            "Outpatient", "Discharged",
        )

        cls._section_title(E, styles, "PART III – ITEMIZED CHARGES / CONSUMPTION OF BENEFITS")
        cls._soa_line_items_table(E, items, subtotal)
        E.append(Paragraph(
            "Note: Unit prices reflect the rate effective on the date each charge was encoded.",
            ParagraphStyle(
                "soa_note", parent=styles["Normal"], fontName=cls._PH_FONT,
                fontSize=cls._PH_FS_SM, textColor=colors.HexColor("#333333"),
            ),
        ))
        E.append(Spacer(1, 6))

        if case_code:
            cls._section_title(E, styles, "PHILHEALTH BENEFITS")
            coverage_label = (
                "Medical Case Rate (ICD-10)" if case_type == "Medical"
                else "Surgical Procedure Case Rate (RVS)"
            )
            rate_as_of = ""
            if ph_effective_date:
                if hasattr(ph_effective_date, "strftime"):
                    rate_as_of = ph_effective_date.strftime("%B %d, %Y")
                else:
                    rate_as_of = str(ph_effective_date)
            cls._field_table(E, [
                ["Coverage Type", coverage_label, "Case Code", case_code],
                ["Case Description", (case_description or "")[:80],
                 "Rate Effective", rate_as_of or "N/A"],
                ["ICD-10 / RVS Code", case_code,
                 "1st Case Rate Amount", f"{case_rate:,.2f}"],
            ])
            cls._charges_table(E, [
                ["Description", "Amount (PHP)"],
                ["PhilHealth Case Rate", f"{case_rate:,.2f}"],
                ["Hospital / Facility Share", f"{health_facility_fee:,.2f}"],
                ["Professional Fee Share", f"{professional_fee_ph:,.2f}"],
                ["PhilHealth Deduction Applied", f"({philhealth_deduction:,.2f})"],
            ])

        cls._section_title(E, styles, "PART IV – BILLING SUMMARY")
        summary = [
            ["Description", "Amount (PHP)"],
            ["Sub-Total", f"{subtotal:,.2f}"],
        ]
        if discount_amount > 0:
            label = f"Discount ({discount_type})" if discount_type else "Discount"
            summary.append([label, f"({discount_amount:,.2f})"])
        if philhealth_deduction > 0:
            summary.append(["PhilHealth Deduction", f"({philhealth_deduction:,.2f})"])
        summary.extend([
            ["Net Amount Due", f"{total_amount:,.2f}"],
            ["Amount Paid", f"{amount_paid:,.2f}"],
            ["Patient Co-Pay / Balance", f"{balance:,.2f}"],
        ])
        cls._charges_table(E, summary)

        cls._cert_block(
            E,
            "PART V – CERTIFICATION",
            "I certify that the services rendered and charges listed are true and correct.\n\n\n"
            "_________________________________________\n"
            "Signature over Printed Name of Authorized HCI Representative\n"
            "Date Signed: ___________________________",
            "Member / Patient Acknowledgment\n"
            "I acknowledge receipt of this Statement of Account.\n\n\n"
            "_________________________________________\n"
            "Signature over Printed Name of Member / Patient\n"
            "Date Signed: ___________________________",
        )

        if footer and footer not in ("—", ""):
            cls._section_title(E, styles, "REMARKS / NOTES")
            E.append(Paragraph(
                footer[:500],
                ParagraphStyle(
                    "soa_footer", parent=styles["Normal"], fontName=cls._PH_FONT,
                    fontSize=cls._PH_FS_SM, textColor=colors.black,
                ),
            ))

        doc.build(E)

    @classmethod
    def _report_icon_flowable(cls, report_key: str, size: float = 0.34 * inch) -> Image:
        icon_path = str(ensure_report_icon_path(report_key, 96))
        return Image(icon_path, width=size, height=size)

    @classmethod
    def _report_data_table(cls, headers: list, rows: list, numeric_cols: set | None = None) -> Table:
        """CF2-style bordered data grid for clinic reports."""
        numeric_cols = numeric_cols or set()
        col_count = max(len(headers), 1)
        col_w = cls._PH_PAGE_W / col_count
        table_rows = [headers] + rows
        t = Table(table_rows, colWidths=[col_w] * col_count, repeatRows=1)
        style_cmds = [
            ("FONTNAME", (0, 0), (-1, -1), cls._PH_FONT),
            ("FONTSIZE", (0, 0), (-1, -1), cls._PH_FS_SM),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
            ("BOX", (0, 0), (-1, -1), 0.5, cls._PH_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, cls._PH_RULE),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("FONTNAME", (0, 0), (-1, 0), cls._PH_FONT_BOLD),
            ("BACKGROUND", (0, 0), (-1, 0), cls._PH_HDR_BG),
        ]
        for col in numeric_cols:
            style_cmds.append(("ALIGN", (col, 1), (col, -1), "RIGHT"))
        for i in range(1, len(table_rows)):
            if i % 2 == 0:
                style_cmds.append(("BACKGROUND", (0, i), (-1, i), cls._PH_ROW_ALT))
        t.setStyle(TableStyle(style_cmds))
        return t

    @classmethod
    def _report_title_block(cls, elements: list, styles, report_key: str, report_title: str) -> None:
        title_style = ParagraphStyle(
            "rpt_title", parent=styles["Normal"], fontName=cls._PH_FONT_BOLD,
            fontSize=cls._PH_FS_TITLE, leading=14, textColor=colors.black,
        )
        title_row = Table(
            [[cls._report_icon_flowable(report_key), Paragraph(report_title, title_style)]],
            colWidths=[0.42 * inch, cls._PH_PAGE_W - 0.42 * inch],
        )
        title_row.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        elements.append(title_row)
        elements.append(Spacer(1, 4))

    @classmethod
    def generate_clinic_report(
        cls,
        output_path: str,
        clinic_name: str,
        clinic_address: str,
        report_key: str,
        report_title: str,
        period_label: str,
        headers: list,
        rows: list,
        summary_rows: list | None = None,
        accreditation_no: str = "",
        report_ref: str = "",
    ) -> None:
        """Generate clinic reports using the same government-style layout as CF2/SOA."""
        doc = cls._ph_doc(output_path, clinic_name, report_title, clinic_name)
        styles = getSampleStyleSheet()
        E = []

        form_label = (
            f"{report_title.upper()}\n"
            "Clinic Management Report\n"
            "Official Facility Data Export"
        )
        cls._philhealth_header(E, styles, clinic_name, form_label, report_ref or "RPT-0001")
        cls._report_title_block(E, styles, report_key, report_title)

        cls._section_title(E, styles, "PART I – HEALTH CARE INSTITUTION (HCI) INFORMATION")
        cls._field_table(E, [
            ["PhilHealth Accreditation No. (PAN)", accreditation_no,
             "Name of Health Care Institution", clinic_name],
            ["Address", clinic_address, "Report Period", period_label],
            ["Date Generated", datetime.now().strftime("%B %d, %Y %I:%M %p"),
             "Total Records", str(len(rows))],
        ])

        if summary_rows:
            cls._section_title(E, styles, "PART II – REPORT SUMMARY")
            cls._charges_table(E, [["Description", "Value"]] + summary_rows)

        cls._section_title(
            E, styles,
            "PART III – DETAILED RECORDS" if summary_rows else "PART II – DETAILED RECORDS",
        )
        if rows:
            numeric_cols = set()
            for idx, header in enumerate(headers):
                label = str(header).lower()
                if any(token in label for token in ("total", "paid", "balance", "price", "stock", "deduction", "amount", "qty")):
                    numeric_cols.add(idx)
            E.append(cls._report_data_table(headers, rows, numeric_cols))
        else:
            E.append(Paragraph(
                "No records found for the selected period.",
                ParagraphStyle(
                    "rpt_empty", parent=styles["Normal"], fontName=cls._PH_FONT,
                    fontSize=cls._PH_FS, textColor=colors.black,
                ),
            ))

        cls._cert_block(
            E,
            "CERTIFICATION",
            "I certify that the information contained in this report is true and correct "
            "based on the clinic records.\n\n\n"
            "_________________________________________\n"
            "Signature over Printed Name of Authorized Representative\n"
            "Date Signed: ___________________________",
            f"Facility: {cls._ph_val(clinic_name)}\n"
            f"Report: {report_title}\n\n\n"
            "_________________________________________\n"
            "Reviewed By\n"
            "Date: ___________________________",
        )
        doc.build(E)

    @staticmethod
    def generate_income_report(
        output_path: str,
        clinic_name: str,
        report_title: str,
        period_label: str,
        rows: list,
        summary: dict,
        clinic_address: str = "",
        accreditation_no: str = "",
        report_key: str = "daily_income",
    ) -> None:
        """Generate a daily / monthly / yearly income report PDF."""
        detail_rows = []
        for r in rows:
            detail_rows.append([
                r.get("date", ""),
                r.get("billing_no", ""),
                r.get("patient", "")[:40],
                f"{float(r.get('total', 0)):,.2f}",
                f"{float(r.get('paid', 0)):,.2f}",
                f"{float(r.get('balance', 0)):,.2f}",
                r.get("status", ""),
            ])

        summary_rows = [
            ["Total Billings (PHP)", f"{float(summary.get('total_billed', 0)):,.2f}"],
            ["Total Collected (PHP)", f"{float(summary.get('total_collected', 0)):,.2f}"],
            ["Outstanding Balance (PHP)", f"{float(summary.get('total_balance', 0)):,.2f}"],
            ["Number of Bills", str(summary.get("count", 0))],
        ]
        ref = f"INC-{datetime.now().strftime('%Y%m%d')}"
        PDFGenerator.generate_clinic_report(
            output_path=output_path,
            clinic_name=clinic_name,
            clinic_address=clinic_address,
            report_key=report_key,
            report_title=report_title,
            period_label=period_label,
            headers=["Date", "Bill No.", "Patient", "Total (PHP)", "Paid (PHP)", "Balance (PHP)", "Status"],
            rows=detail_rows,
            summary_rows=summary_rows,
            accreditation_no=accreditation_no,
            report_ref=ref,
        )
