"""PDF document generators for receipts, prescriptions, and patient profiles."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


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
