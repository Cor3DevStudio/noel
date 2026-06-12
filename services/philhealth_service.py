"""PhilHealth benefit computation service."""

import json
import zipfile
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from config.settings import ECLAIMS_DIR, PWD_DISCOUNT_RATE, SENIOR_DISCOUNT_RATE
from models.philhealth import PhilHealthClaimForm, PhilHealthRecord, PhilHealthTransaction
from repositories.patient_repository import PatientRepository
from repositories.philhealth_repository import (
    PhilHealthClaimFormRepository,
    PhilHealthRepository,
    PhilHealthTransactionRepository,
)
from services.activity_service import ActivityService
from utils.security import session_manager


ECLAIM_DOCUMENT_TYPES = [
    "CF1",
    "CF2",
    "CF3",
    "CF4",
    "CF5",
    "SOA XML",
    "SOA PDF",
    "Signature Form",
    "Annex A - Medical Case Rates",
    "Annex B - Procedure Case Rates",
    "Receipt",
    "Other",
]


def guess_eclaim_document_type(path: str, default_form_type: str | None = None) -> str:
    """Infer PhilHealth document type from filename."""
    name = Path(path).name.lower().replace(" ", "").replace("_", "").replace("-", "")

    if name.endswith(".xml") or ("soa" in name and name.endswith(".xml")):
        return "SOA XML"
    if "soa" in name and name.endswith(".pdf"):
        return "SOA PDF"
    if "signature" in name or name.startswith("csf"):
        return "Signature Form"
    if "annexa" in name or "medicalcaserates" in name or "listofmedical" in name:
        return "Annex A - Medical Case Rates"
    if "annexb" in name or "procedurecaserates" in name or "listofprocedure" in name:
        return "Annex B - Procedure Case Rates"
    if "receipt" in name:
        return "Receipt"

    for code in ("cf1", "cf2", "cf3", "cf4", "cf5"):
        if code in name or f"claimform{code[-1]}" in name or f"philhealthclaimform{code[-1]}" in name:
            return code.upper()

    if default_form_type and default_form_type in ECLAIM_DOCUMENT_TYPES:
        return default_form_type
    return "Other"


def normalize_supporting_docs(
    raw,
    default_form_type: str | None = None,
) -> List[Dict[str, str]]:
    """Convert stored JSON (legacy path strings or typed objects) to uniform entries."""
    if not raw:
        return []

    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return []

    entries: List[Dict[str, str]] = []
    for item in raw:
        if isinstance(item, str):
            entries.append({
                "path": item,
                "doc_type": guess_eclaim_document_type(item, default_form_type),
            })
        elif isinstance(item, dict):
            path = item.get("path") or item.get("file") or ""
            if not path:
                continue
            doc_type = item.get("doc_type") or item.get("document_type") or ""
            if doc_type not in ECLAIM_DOCUMENT_TYPES:
                doc_type = guess_eclaim_document_type(path, default_form_type)
            entries.append({"path": path, "doc_type": doc_type})
    return entries


class PhilHealthService:
    def __init__(self, session: Session, activity_service: ActivityService | None = None) -> None:
        self.session = session
        self.activity = activity_service or ActivityService(session)
        self.rate_repo = PhilHealthRepository(session)
        self.transaction_repo = PhilHealthTransactionRepository(session)
        self.patient_repo = PatientRepository(session)
        self.claim_form_repo = PhilHealthClaimFormRepository(session)

    def compute_benefits(
        self,
        patient_id: int,
        case_rate_id: int,
        total_bill: Decimal,
        apply_senior: bool = True,
        apply_pwd: bool = True,
    ) -> Dict[str, Decimal]:
        """Compute PhilHealth benefit breakdown."""
        patient = self.patient_repo.get_by_id(patient_id)
        case_rate = self.rate_repo.get_by_id(case_rate_id)
        if not patient or not case_rate:
            return {}

        total_bill = Decimal(str(total_bill))
        case_rate_amount = Decimal(str(case_rate.case_rate))
        hospital_pct = Decimal(str(case_rate.hospital_share_pct)) / Decimal("100")
        prof_pct = Decimal(str(case_rate.professional_fee_pct)) / Decimal("100")

        hospital_share = (case_rate_amount * hospital_pct).quantize(Decimal("0.01"), ROUND_HALF_UP)
        professional_fee = (case_rate_amount * prof_pct).quantize(Decimal("0.01"), ROUND_HALF_UP)
        philhealth_deduction = min(case_rate_amount, total_bill)

        remaining = total_bill - philhealth_deduction
        senior_discount = Decimal("0")
        pwd_discount = Decimal("0")

        if apply_senior and patient.is_senior_citizen:
            senior_discount = (remaining * Decimal(str(SENIOR_DISCOUNT_RATE))).quantize(
                Decimal("0.01"), ROUND_HALF_UP
            )
            remaining -= senior_discount
        elif apply_pwd and patient.is_pwd:
            pwd_discount = (remaining * Decimal(str(PWD_DISCOUNT_RATE))).quantize(
                Decimal("0.01"), ROUND_HALF_UP
            )
            remaining -= pwd_discount

        patient_balance = max(Decimal("0"), remaining).quantize(Decimal("0.01"), ROUND_HALF_UP)

        return {
            "case_rate_amount": case_rate_amount,
            "hospital_share": hospital_share,
            "professional_fee": professional_fee,
            "philhealth_deduction": philhealth_deduction,
            "senior_discount": senior_discount,
            "pwd_discount": pwd_discount,
            "patient_balance": patient_balance,
            "total_bill": total_bill,
        }

    def process_transaction(
        self,
        patient_id: int,
        case_rate_id: int,
        total_bill: Decimal,
        billing_id: int | None = None,
        consultation_id: int | None = None,
        notes: str = "",
    ) -> Tuple[bool, str, Optional[PhilHealthTransaction]]:
        patient = self.patient_repo.get_by_id(patient_id)
        if not patient:
            return False, "Patient not found.", None
        if not patient.philhealth_number:
            return False, "Patient has no PhilHealth number on file.", None

        computation = self.compute_benefits(patient_id, case_rate_id, total_bill)
        if not computation:
            return False, "Unable to compute PhilHealth benefits.", None

        user = session_manager.get_current_user()
        transaction = self.transaction_repo.create({
            "patient_id": patient_id,
            "billing_id": billing_id,
            "consultation_id": consultation_id,
            "case_rate_id": case_rate_id,
            "philhealth_number": patient.philhealth_number,
            "case_rate_amount": computation["case_rate_amount"],
            "hospital_share": computation["hospital_share"],
            "professional_fee": computation["professional_fee"],
            "philhealth_deduction": computation["philhealth_deduction"],
            "patient_balance": computation["patient_balance"],
            "senior_discount": computation["senior_discount"],
            "pwd_discount": computation["pwd_discount"],
            "total_bill": computation["total_bill"],
            "notes": notes,
            "processed_by": user["id"] if user else None,
        })
        self.activity.log(
            "CREATE", "PhilHealth",
            f"Processed PhilHealth transaction for patient #{patient_id} — deduction ₱{computation['philhealth_deduction']}",
        )
        return True, "PhilHealth transaction processed.", transaction

    def get_case_rates(self) -> list[PhilHealthRecord]:
        return self.rate_repo.get_active_rates()

    def search_rates(
        self, query: str = "", case_type: str = "All", page: int = 1, per_page: int = 50
    ):
        """Search/filter case rates with pagination. Returns (records, total)."""
        return self.rate_repo.search(query, case_type, page, per_page)

    def get_type_counts(self) -> dict:
        return self.rate_repo.get_type_counts()

    def get_rates_by_codes(self, codes: List[str]) -> Dict[str, PhilHealthRecord]:
        rows = self.rate_repo.get_by_codes(codes)
        return {r.case_code: r for r in rows}

    def create_case_rate(self, data: dict) -> Tuple[bool, str]:
        from utils.helpers import validate_money_amount

        if self.rate_repo.get_by_code(data["case_code"]):
            return False, "Case code already exists."
        for field, label in (
            ("case_rate", "Case rate"),
            ("health_facility_fee", "Health facility fee"),
            ("professional_fee_amount", "Professional fee"),
        ):
            ok, msg = validate_money_amount(Decimal(str(data.get(field, 0))), label)
            if not ok:
                return False, msg
        data.setdefault("price_effective_date", date.today())
        self.rate_repo.create(data)
        self.activity.log("CREATE", "PhilHealth", f"Created case rate {data['case_code']}")
        return True, "Case rate created successfully."

    def update_case_rate(self, rate_id: int, data: dict) -> Tuple[bool, str]:
        from utils.helpers import validate_money_amount

        rate = self.rate_repo.get_by_id(rate_id)
        if not rate:
            return False, "Case rate not found."
        for field, label in (
            ("case_rate", "Case rate"),
            ("health_facility_fee", "Health facility fee"),
            ("professional_fee_amount", "Professional fee"),
        ):
            if field in data:
                ok, msg = validate_money_amount(Decimal(str(data[field])), label)
                if not ok:
                    return False, msg
        price_fields = ("case_rate", "health_facility_fee", "professional_fee_amount")
        price_changed = any(
            f in data and Decimal(str(data[f])) != Decimal(str(getattr(rate, f) or 0))
            for f in price_fields
        )
        if price_changed:
            data["price_effective_date"] = date.today()
        self.rate_repo.update(rate, data)
        self.activity.log("UPDATE", "PhilHealth", f"Updated case rate {rate.case_code}")
        return True, "Case rate updated successfully."

    def delete_case_rate(self, rate_id: int) -> Tuple[bool, str]:
        rate = self.rate_repo.get_by_id(rate_id)
        if not rate:
            return False, "Case rate not found."
        code = rate.case_code
        self.rate_repo.delete(rate)
        self.activity.log("DELETE", "PhilHealth", f"Deleted case rate {code}")
        return True, "Case rate deleted."

    def get_patient_history(self, patient_id: int) -> list[PhilHealthTransaction]:
        return self.transaction_repo.get_by_patient(patient_id)

    # ------------------------------------------------------------------ #
    #  Claim Forms  CF2 / CF3 / CF4 / CF5                                  #
    # ------------------------------------------------------------------ #

    def _generate_form_number(self, form_type: str) -> str:
        today = datetime.now().strftime("%Y%m%d")
        existing = self.claim_form_repo.get_by_form_type(form_type)
        seq = len(existing) + 1
        return f"{form_type}-{today}-{seq:04d}"

    def create_claim_form(self, form_type: str, data: dict) -> Tuple[bool, str, Optional[PhilHealthClaimForm]]:
        """Create a new CF2/CF3/CF4/CF5 claim form."""
        valid_types = ("CF2", "CF3", "CF4", "CF5")
        if form_type not in valid_types:
            return False, f"Invalid form type. Must be one of: {', '.join(valid_types)}", None

        patient = self.patient_repo.get_by_id(data.get("patient_id", 0))
        if not patient:
            return False, "Patient not found.", None

        user = session_manager.get_current_user()
        payload = {
            "form_number": self._generate_form_number(form_type),
            "form_type": form_type,
            "status": "Draft",
            "patient_id": patient.id,
            "philhealth_number": data.get("philhealth_number") or patient.philhealth_number,
            "date_of_claim": data.get("date_of_claim") or date.today(),
            "diagnosis": data.get("diagnosis"),
            "icd_code": data.get("icd_code"),
            "case_rate_code": data.get("case_rate_code"),
            "total_amount_claimed": Decimal(str(data.get("total_amount_claimed", 0))),
            "transaction_id": data.get("transaction_id"),
            "notes": data.get("notes"),
            "prepared_by": user["id"] if user else None,
        }

        # CF2 / CF4 – facility fields
        if form_type in ("CF2", "CF4"):
            payload.update({
                "admission_date": data.get("admission_date"),
                "discharge_date": data.get("discharge_date"),
                "type_of_admission": data.get("type_of_admission", "Ordinary"),
                "room_charges": Decimal(str(data.get("room_charges", 0))),
                "medicine_charges": Decimal(str(data.get("medicine_charges", 0))),
                "xray_lab_charges": Decimal(str(data.get("xray_lab_charges", 0))),
                "other_charges": Decimal(str(data.get("other_charges", 0))),
                "hospital_share": Decimal(str(data.get("hospital_share", 0))),
            })

        # CF3 – professional fee
        if form_type == "CF3":
            payload.update({
                "physician_name": data.get("physician_name"),
                "physician_prc_no": data.get("physician_prc_no"),
                "physician_ptr_no": data.get("physician_ptr_no"),
                "physician_philhealth_no": data.get("physician_philhealth_no"),
                "type_of_claim": data.get("type_of_claim", "Primary"),
                "professional_fee_claimed": Decimal(str(data.get("professional_fee_claimed", 0))),
                "professional_fee_share": Decimal(str(data.get("professional_fee_share", 0))),
            })

        # CF5 – ESRD / dialysis
        if form_type == "CF5":
            payload.update({
                "dialysis_center_name": data.get("dialysis_center_name"),
                "dialysis_center_accreditation": data.get("dialysis_center_accreditation"),
                "period_from": data.get("period_from"),
                "period_to": data.get("period_to"),
                "number_of_sessions": data.get("number_of_sessions"),
                "dialysis_type": data.get("dialysis_type", "Hemodialysis"),
            })

        form = self.claim_form_repo.create(payload)
        self.activity.log(
            "CREATE", "PhilHealth",
            f"Created {form_type} claim form {form.form_number} for patient #{patient.id}",
        )
        return True, f"{form_type} claim form {form.form_number} created.", form

    def update_claim_form_status(self, form_id: int, status: str) -> Tuple[bool, str]:
        form = self.claim_form_repo.get_by_id(form_id)
        if not form:
            return False, "Claim form not found."
        self.claim_form_repo.update(form, {"status": status})
        self.activity.log(
            "UPDATE", "PhilHealth",
            f"Updated {form.form_type} {form.form_number} status to {status}",
        )
        return True, f"Status updated to '{status}'."

    def get_claim_forms_for_patient(self, patient_id: int) -> List[PhilHealthClaimForm]:
        return self.claim_form_repo.get_by_patient(patient_id)

    def get_all_claim_forms(self) -> List[PhilHealthClaimForm]:
        return self.claim_form_repo.get_all()

    def get_claim_form_by_id(self, form_id: int) -> Optional[PhilHealthClaimForm]:
        return self.claim_form_repo.get_by_id(form_id)

    def delete_claim_form(self, form_id: int) -> Tuple[bool, str]:
        form = self.claim_form_repo.get_by_id(form_id)
        if not form:
            return False, "Claim form not found."
        if form.status == "Submitted":
            return False, "Cannot delete a submitted claim form."
        label = f"{form.form_type} {form.form_number}"
        self.claim_form_repo.delete(form)
        self.activity.log("DELETE", "PhilHealth", f"Deleted claim form {label}")
        return True, "Claim form deleted."

    # ------------------------------------------------------------------ #
    #  eClaims Transmission                                                #
    # ------------------------------------------------------------------ #

    def transmit_eclaim(
        self,
        form_id: int,
        docs,
        notes: str = "",
    ) -> Tuple[bool, str, Optional[str]]:
        """Bundle claim docs into a ZIP package and mark claim as Transmitted."""
        form = self.claim_form_repo.get_by_id(form_id)
        if not form:
            return False, "Claim form not found.", None

        entries = normalize_supporting_docs(docs, form.form_type)
        patient = form.patient
        now = datetime.now()
        ref_no = f"ECLAIM-{now.strftime('%Y%m%d%H%M%S')}-{form.id:04d}"

        # Per-claim output folder
        out_dir = Path(ECLAIMS_DIR) / form.form_number
        out_dir.mkdir(parents=True, exist_ok=True)

        # Write manifest
        manifest = {
            "eclaim_ref_no": ref_no,
            "form_number": form.form_number,
            "form_type": form.form_type,
            "patient_name": patient.full_name if patient else "—",
            "philhealth_number": form.philhealth_number or "—",
            "diagnosis": form.diagnosis or "—",
            "icd_code": form.icd_code or "—",
            "case_rate_code": form.case_rate_code or "—",
            "total_amount_claimed": str(form.total_amount_claimed),
            "date_of_claim": str(form.date_of_claim or "—"),
            "transmitted_at": now.isoformat(),
            "supporting_docs": [
                {
                    "file": Path(entry["path"]).name,
                    "document_type": entry["doc_type"],
                }
                for entry in entries
            ],
            "notes": notes,
        }
        manifest_path = out_dir / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        # ZIP package — SOA XML first, then PDFs and other files
        zip_path = Path(ECLAIMS_DIR) / f"{form.form_number}.zip"
        sorted_docs = sorted(
            entries,
            key=lambda e: (
                0 if str(e["path"]).lower().endswith(".xml") else 1,
                Path(e["path"]).name,
            ),
        )
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(manifest_path, "manifest.json")
            for entry in sorted_docs:
                p = Path(entry["path"])
                if p.exists():
                    zf.write(p, p.name)

        # Persist changes
        self.claim_form_repo.update(form, {
            "eclaim_ref_no":      ref_no,
            "eclaim_submitted_at": now,
            "eclaim_status":      "Transmitted",
            "supporting_docs":    json.dumps(entries),
            "eclaim_notes":       notes,
            "status":             "Submitted",
        })

        self.activity.log(
            "TRANSMIT", "PhilHealth",
            f"Transmitted eClaim {form.form_number} — ref {ref_no}",
        )
        return True, f"eClaim package created. Ref: {ref_no}", str(zip_path)

    def update_eclaim_status(self, form_id: int, eclaim_status: str) -> Tuple[bool, str]:
        """Manually update the eClaim transmission status (Acknowledged / Rejected)."""
        form = self.claim_form_repo.get_by_id(form_id)
        if not form:
            return False, "Claim form not found."
        self.claim_form_repo.update(form, {"eclaim_status": eclaim_status})
        self.activity.log(
            "UPDATE", "PhilHealth",
            f"Updated eClaim status for {form.form_number} to {eclaim_status}",
        )
        return True, f"eClaim status updated to '{eclaim_status}'."

    def get_active_claim_for_patient(self, patient_id: int):
        return self.claim_form_repo.get_active_claim_for_patient(patient_id)

    def add_supporting_doc(
        self, form_id: int, doc_path: str, doc_type: str | None = None,
    ) -> Tuple[bool, str]:
        """Append a supporting document to a claim form (deduplicated)."""
        form = self.claim_form_repo.get_by_id(form_id)
        if not form:
            return False, "Claim form not found."
        docs = normalize_supporting_docs(form.supporting_docs, form.form_type)
        resolved = str(Path(doc_path).resolve())
        existing_paths = {d["path"] for d in docs}
        if resolved not in existing_paths and doc_path not in existing_paths:
            inferred = doc_type or guess_eclaim_document_type(doc_path, form.form_type)
            docs.insert(0, {"path": resolved, "doc_type": inferred})
        self.claim_form_repo.update(form, {"supporting_docs": json.dumps(docs)})
        return True, "Document attached to eClaim."

    def update_supporting_docs(self, form_id: int, docs: list) -> Tuple[bool, str]:
        """Save supporting document list with document types."""
        form = self.claim_form_repo.get_by_id(form_id)
        if not form:
            return False, "Claim form not found."
        entries = normalize_supporting_docs(docs, form.form_type)
        self.claim_form_repo.update(form, {"supporting_docs": json.dumps(entries)})
        return True, "Supporting documents updated."

    def attach_soa_xml_to_eclaim(
        self, patient_id: int, xml_path: str
    ) -> Tuple[bool, str, Optional[str]]:
        """Link SOA XML to the patient's active claim form supporting documents."""
        form = self.claim_form_repo.get_active_claim_for_patient(patient_id)
        if not form:
            return False, (
                "No claim form found for this patient. "
                "Create a CF2/CF3/CF4 claim in PhilHealth first."
            ), None
        ok, msg = self.add_supporting_doc(form.id, xml_path, doc_type="SOA XML")
        if not ok:
            return False, msg, None
        return True, f"SOA XML attached to {form.form_number}.", form.form_number
