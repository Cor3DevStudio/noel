"""Generate Statement of Account (SOA) XML for PhilHealth eClaims transmission."""

from datetime import datetime
from pathlib import Path
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, tostring


class SoaXmlGenerator:
    @staticmethod
    def generate(output_path: str, data: dict) -> str:
        """Write SOA XML file. Returns the absolute path written."""
        root = Element("StatementOfAccount")
        root.set("xmlns", "http://www.philhealth.gov.ph/eclaims/soa")
        root.set("version", "1.0")

        header = SubElement(root, "Header")
        SubElement(header, "SOANumber").text = str(data.get("soa_number", ""))
        SubElement(header, "BillingNumber").text = str(data.get("billing_number", ""))
        SubElement(header, "GeneratedAt").text = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        SubElement(header, "ClinicName").text = str(data.get("clinic_name", ""))
        SubElement(header, "ClinicAddress").text = str(data.get("clinic_address", ""))

        patient = SubElement(root, "Patient")
        SubElement(patient, "Name").text = str(data.get("patient_name", ""))
        SubElement(patient, "PhilHealthNumber").text = str(data.get("philhealth_number", ""))
        SubElement(patient, "AdmissionDate").text = str(data.get("admission_date", ""))
        SubElement(patient, "DischargeDate").text = str(data.get("discharge_date", ""))

        charges = SubElement(root, "Charges")
        for item in data.get("items", []):
            line = SubElement(charges, "LineItem")
            SubElement(line, "Description").text = str(item.get("description", ""))
            SubElement(line, "Type").text = str(item.get("item_type", ""))
            SubElement(line, "Quantity").text = str(item.get("quantity", 1))
            SubElement(line, "UnitPrice").text = f"{float(item.get('unit_price', 0)):.2f}"
            SubElement(line, "TotalPrice").text = f"{float(item.get('total_price', 0)):.2f}"
            as_of = item.get("price_as_of")
            if as_of:
                SubElement(line, "PriceAsOf").text = str(as_of)

        ph = SubElement(root, "PhilHealthCoverage")
        SubElement(ph, "CaseCode").text = str(data.get("case_code", ""))
        SubElement(ph, "CaseDescription").text = str(data.get("case_description", ""))
        SubElement(ph, "CaseType").text = str(data.get("case_type", ""))
        SubElement(ph, "CaseRate").text = f"{float(data.get('case_rate', 0)):.2f}"
        SubElement(ph, "HealthFacilityFee").text = f"{float(data.get('health_facility_fee', 0)):.2f}"
        SubElement(ph, "ProfessionalFee").text = f"{float(data.get('professional_fee_ph', 0)):.2f}"
        SubElement(ph, "DeductionApplied").text = f"{float(data.get('philhealth_deduction', 0)):.2f}"
        if data.get("ph_effective_date"):
            SubElement(ph, "RateAsOf").text = str(data["ph_effective_date"])

        summary = SubElement(root, "Summary")
        SubElement(summary, "Subtotal").text = f"{float(data.get('subtotal', 0)):.2f}"
        SubElement(summary, "DiscountAmount").text = f"{float(data.get('discount_amount', 0)):.2f}"
        SubElement(summary, "DiscountType").text = str(data.get("discount_type", ""))
        SubElement(summary, "PhilHealthDeduction").text = f"{float(data.get('philhealth_deduction', 0)):.2f}"
        SubElement(summary, "TotalAmount").text = f"{float(data.get('total_amount', 0)):.2f}"
        SubElement(summary, "AmountPaid").text = f"{float(data.get('amount_paid', 0)):.2f}"
        SubElement(summary, "Balance").text = f"{float(data.get('balance', 0)):.2f}"

        raw = tostring(root, encoding="unicode")
        pretty = minidom.parseString(raw).toprettyxml(indent="  ", encoding="UTF-8")

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(pretty)
        return str(out.resolve())
