"""Seed script — PhilHealth case rates, patients, and demo claim forms (CF2–CF5)."""

import sys
from datetime import date, datetime
from decimal import Decimal

sys.path.insert(0, ".")

from database.connection import get_db_session, init_db
from models.patient import Patient
from models.philhealth import PhilHealthClaimForm, PhilHealthRecord


# ─────────────────────────────────────────────────────────────────────────────
#  PhilHealth Case Rate Records
# ─────────────────────────────────────────────────────────────────────────────
CASE_RATES = [
    {"case_code": "Z00.00", "case_description": "General Medical Examination", "case_rate": Decimal("2000.00"), "hospital_share_pct": Decimal("70"), "professional_fee_pct": Decimal("30")},
    {"case_code": "J18.9",  "case_description": "Pneumonia, Unspecified",       "case_rate": Decimal("9000.00"), "hospital_share_pct": Decimal("70"), "professional_fee_pct": Decimal("30")},
    {"case_code": "I10",    "case_description": "Essential Hypertension",        "case_rate": Decimal("6500.00"), "hospital_share_pct": Decimal("70"), "professional_fee_pct": Decimal("30")},
    {"case_code": "E11.9",  "case_description": "Type 2 Diabetes Mellitus",     "case_rate": Decimal("7000.00"), "hospital_share_pct": Decimal("70"), "professional_fee_pct": Decimal("30")},
    {"case_code": "K80.20", "case_description": "Cholelithiasis / Gallstones",  "case_rate": Decimal("12000.00"),"hospital_share_pct": Decimal("70"), "professional_fee_pct": Decimal("30")},
    {"case_code": "N18.3",  "case_description": "Chronic Kidney Disease Stage 3","case_rate": Decimal("11000.00"),"hospital_share_pct": Decimal("70"), "professional_fee_pct": Decimal("30")},
    {"case_code": "Z49.1",  "case_description": "Hemodialysis (per session)",    "case_rate": Decimal("3200.00"), "hospital_share_pct": Decimal("65"), "professional_fee_pct": Decimal("35")},
    {"case_code": "S72.00", "case_description": "Fracture of Femoral Neck",     "case_rate": Decimal("20000.00"),"hospital_share_pct": Decimal("70"), "professional_fee_pct": Decimal("30")},
    {"case_code": "C50.9",  "case_description": "Breast Cancer",                "case_rate": Decimal("15000.00"),"hospital_share_pct": Decimal("70"), "professional_fee_pct": Decimal("30")},
    {"case_code": "O82",    "case_description": "Cesarean Section Delivery",    "case_rate": Decimal("19000.00"),"hospital_share_pct": Decimal("70"), "professional_fee_pct": Decimal("30")},
]


# ─────────────────────────────────────────────────────────────────────────────
#  Demo Patients (with full PhilHealth info)
# ─────────────────────────────────────────────────────────────────────────────
PATIENTS = [
    {
        "patient_number":          "PH-2026-001",
        "first_name":              "Maria",
        "middle_name":             "Santos",
        "last_name":               "Reyes",
        "birth_date":              date(1985, 3, 14),
        "gender":                  "Female",
        "civil_status":            "Married",
        "contact_number":          "09171234501",
        "address_street":          "123 Rizal St.",
        "address_barangay":        "Barangay 1",
        "address_city":            "Manila",
        "address_province":        "Metro Manila",
        "philhealth_number":       "04-123456789-0",
        "philhealth_category":     "Employed",
        "philhealth_member_type":  "Member",
        "is_senior_citizen":       False,
        "is_pwd":                  False,
    },
    {
        "patient_number":          "PH-2026-002",
        "first_name":              "Jose",
        "middle_name":             "Cruz",
        "last_name":               "Dela Torre",
        "birth_date":              date(1948, 7, 22),
        "gender":                  "Male",
        "civil_status":            "Widowed",
        "contact_number":          "09181234502",
        "address_street":          "456 Mabini Ave.",
        "address_barangay":        "Barangay 5",
        "address_city":            "Quezon City",
        "address_province":        "Metro Manila",
        "philhealth_number":       "04-234567890-1",
        "philhealth_category":     "Senior Citizen",
        "philhealth_member_type":  "Member",
        "is_senior_citizen":       True,
        "senior_id_number":        "SC-2024-00123",
        "is_pwd":                  False,
    },
    {
        "patient_number":          "PH-2026-003",
        "first_name":              "Ana",
        "middle_name":             "Bautista",
        "last_name":               "Garcia",
        "birth_date":              date(1992, 11, 5),
        "gender":                  "Female",
        "civil_status":            "Single",
        "contact_number":          "09191234503",
        "address_street":          "789 Bonifacio Blvd.",
        "address_barangay":        "Barangay 10",
        "address_city":            "Pasig",
        "address_province":        "Metro Manila",
        "philhealth_number":       "04-345678901-2",
        "philhealth_category":     "Indigent",
        "philhealth_member_type":  "Dependent",
        "is_senior_citizen":       False,
        "is_pwd":                  True,
        "pwd_id_number":           "PWD-2023-00456",
    },
    {
        "patient_number":          "PH-2026-004",
        "first_name":              "Carlos",
        "middle_name":             "Mendoza",
        "last_name":               "Lim",
        "birth_date":              date(1978, 1, 30),
        "gender":                  "Male",
        "civil_status":            "Married",
        "contact_number":          "09201234504",
        "address_street":          "22 Luna St.",
        "address_barangay":        "Barangay 3",
        "address_city":            "Makati",
        "address_province":        "Metro Manila",
        "philhealth_number":       "04-456789012-3",
        "philhealth_category":     "Self-Employed",
        "philhealth_member_type":  "Member",
        "is_senior_citizen":       False,
        "is_pwd":                  False,
    },
    {
        "patient_number":          "PH-2026-005",
        "first_name":              "Rosa",
        "middle_name":             "Flores",
        "last_name":               "Villanueva",
        "birth_date":              date(1965, 6, 18),
        "gender":                  "Female",
        "civil_status":            "Separated",
        "contact_number":          "09211234505",
        "address_street":          "55 Aguinaldo St.",
        "address_barangay":        "Barangay 7",
        "address_city":            "Caloocan",
        "address_province":        "Metro Manila",
        "philhealth_number":       "04-567890123-4",
        "philhealth_category":     "Employed",
        "philhealth_member_type":  "Dependent",
        "is_senior_citizen":       False,
        "is_pwd":                  False,
    },
    {
        "patient_number":          "PH-2026-006",
        "first_name":              "Ramon",
        "middle_name":             None,
        "last_name":               "Aquino",
        "birth_date":              date(1950, 9, 3),
        "gender":                  "Male",
        "civil_status":            "Married",
        "contact_number":          "09221234506",
        "address_street":          "88 Magsaysay Rd.",
        "address_barangay":        "Barangay 12",
        "address_city":            "Taguig",
        "address_province":        "Metro Manila",
        "philhealth_number":       "04-678901234-5",
        "philhealth_category":     "Senior Citizen",
        "philhealth_member_type":  "Member",
        "is_senior_citizen":       True,
        "senior_id_number":        "SC-2023-00789",
        "is_pwd":                  False,
    },
]


# ─────────────────────────────────────────────────────────────────────────────
#  Demo Claim Forms — one per form type, various statuses
# ─────────────────────────────────────────────────────────────────────────────
# Built dynamically after patients are inserted; keyed by patient_number
CLAIM_FORMS = [
    # CF2 – Hospital / Facility Claim — Approved
    {
        "form_number":          "CF2-20260101-0001",
        "form_type":            "CF2",
        "status":               "Approved",
        "patient_number":       "PH-2026-002",   # Jose Dela Torre (Senior)
        "diagnosis":            "Pneumonia, Unspecified",
        "icd_code":             "J18.9",
        "case_rate_code":       "J18.9",
        "total_amount_claimed": Decimal("9000.00"),
        "date_of_claim":        date(2026, 5, 10),
        "admission_date":       date(2026, 5, 5),
        "discharge_date":       date(2026, 5, 9),
        "type_of_admission":    "Ordinary",
        "room_charges":         Decimal("3500.00"),
        "medicine_charges":     Decimal("2800.00"),
        "xray_lab_charges":     Decimal("1200.00"),
        "other_charges":        Decimal("500.00"),
        "hospital_share":       Decimal("6300.00"),
        "notes":                "Senior citizen patient. Full PhilHealth benefit applied.",
    },
    # CF2 – Hospital / Facility Claim — Draft
    {
        "form_number":          "CF2-20260601-0002",
        "form_type":            "CF2",
        "status":               "Draft",
        "patient_number":       "PH-2026-006",   # Ramon Aquino (Senior)
        "diagnosis":            "Essential Hypertension with Chest Pain",
        "icd_code":             "I10",
        "case_rate_code":       "I10",
        "total_amount_claimed": Decimal("6500.00"),
        "date_of_claim":        date(2026, 6, 1),
        "admission_date":       date(2026, 5, 28),
        "discharge_date":       date(2026, 5, 31),
        "type_of_admission":    "Emergency",
        "room_charges":         Decimal("2400.00"),
        "medicine_charges":     Decimal("1800.00"),
        "xray_lab_charges":     Decimal("900.00"),
        "other_charges":        Decimal("400.00"),
        "hospital_share":       Decimal("4550.00"),
        "notes":                "Pending physician countersignature.",
    },
    # CF3 – Professional Fee Claim — Submitted
    {
        "form_number":          "CF3-20260515-0001",
        "form_type":            "CF3",
        "status":               "Submitted",
        "patient_number":       "PH-2026-001",   # Maria Reyes
        "diagnosis":            "Type 2 Diabetes Mellitus — Routine Follow-up",
        "icd_code":             "E11.9",
        "case_rate_code":       "E11.9",
        "total_amount_claimed": Decimal("3500.00"),
        "date_of_claim":        date(2026, 5, 15),
        "physician_name":       "Dr. Maria Santos Reyes",
        "physician_prc_no":     "PRC-0123456",
        "physician_ptr_no":     "PTR-2026-00789",
        "physician_philhealth_no": "PH-DOC-00456",
        "type_of_claim":        "Primary",
        "professional_fee_claimed": Decimal("3500.00"),
        "professional_fee_share":   Decimal("2100.00"),
        "notes":                "Professional fee claim for endocrinology consultation.",
    },
    # CF3 – Professional Fee Claim — Approved
    {
        "form_number":          "CF3-20260520-0002",
        "form_type":            "CF3",
        "status":               "Approved",
        "patient_number":       "PH-2026-004",   # Carlos Lim
        "diagnosis":            "Cholelithiasis — Post-cholecystectomy",
        "icd_code":             "K80.20",
        "case_rate_code":       "K80.20",
        "total_amount_claimed": Decimal("5000.00"),
        "date_of_claim":        date(2026, 5, 20),
        "physician_name":       "Dr. Jose Andres Santos",
        "physician_prc_no":     "PRC-0654321",
        "physician_ptr_no":     "PTR-2026-01122",
        "physician_philhealth_no": "PH-DOC-00891",
        "type_of_claim":        "Specialist",
        "professional_fee_claimed": Decimal("5000.00"),
        "professional_fee_share":   Decimal("3600.00"),
        "notes":                "Surgery performed at facility. Specialist fee claim.",
    },
    # CF4 – All Case Rates / Outpatient — Draft
    {
        "form_number":          "CF4-20260601-0001",
        "form_type":            "CF4",
        "status":               "Draft",
        "patient_number":       "PH-2026-003",   # Ana Garcia (PWD)
        "diagnosis":            "General Medical Examination — Annual",
        "icd_code":             "Z00.00",
        "case_rate_code":       "Z00.00",
        "total_amount_claimed": Decimal("2000.00"),
        "date_of_claim":        date(2026, 6, 5),
        "room_charges":         Decimal("800.00"),
        "medicine_charges":     Decimal("600.00"),
        "xray_lab_charges":     Decimal("400.00"),
        "other_charges":        Decimal("200.00"),
        "hospital_share":       Decimal("1400.00"),
        "notes":                "PWD patient. Outpatient annual checkup.",
    },
    # CF4 – All Case Rates / Outpatient — Submitted
    {
        "form_number":          "CF4-20260608-0002",
        "form_type":            "CF4",
        "status":               "Submitted",
        "patient_number":       "PH-2026-005",   # Rosa Villanueva
        "diagnosis":            "Hypertension Maintenance Check",
        "icd_code":             "I10",
        "case_rate_code":       "I10",
        "total_amount_claimed": Decimal("4500.00"),
        "date_of_claim":        date(2026, 6, 8),
        "room_charges":         Decimal("1500.00"),
        "medicine_charges":     Decimal("1200.00"),
        "xray_lab_charges":     Decimal("600.00"),
        "other_charges":        Decimal("200.00"),
        "hospital_share":       Decimal("3500.00"),
        "notes":                "Submitted for PhilHealth reimbursement.",
    },
    # CF5 – ESRD / Dialysis — Approved
    {
        "form_number":          "CF5-20260501-0001",
        "form_type":            "CF5",
        "status":               "Approved",
        "patient_number":       "PH-2026-002",   # Jose Dela Torre (Senior)
        "diagnosis":            "Chronic Kidney Disease Stage 3 — Hemodialysis",
        "icd_code":             "N18.3",
        "case_rate_code":       "Z49.1",
        "total_amount_claimed": Decimal("32000.00"),
        "date_of_claim":        date(2026, 5, 31),
        "dialysis_center_name":           "Metro Kidney Care Center",
        "dialysis_center_accreditation":  "MKCC-ACC-2024-00123",
        "dialysis_type":                  "Hemodialysis",
        "period_from":                    date(2026, 5, 1),
        "period_to":                      date(2026, 5, 31),
        "number_of_sessions":             10,
        "notes":                "10 sessions at ₱3,200 per session. PhilHealth benefit fully applied.",
    },
    # CF5 – ESRD / Dialysis — Draft
    {
        "form_number":          "CF5-20260610-0002",
        "form_type":            "CF5",
        "status":               "Draft",
        "patient_number":       "PH-2026-006",   # Ramon Aquino (Senior)
        "diagnosis":            "End-Stage Renal Disease — Peritoneal Dialysis",
        "icd_code":             "N18.3",
        "case_rate_code":       "Z49.1",
        "total_amount_claimed": Decimal("19200.00"),
        "date_of_claim":        date(2026, 6, 10),
        "dialysis_center_name":           "National Dialysis & Nephrology Center",
        "dialysis_center_accreditation":  "NDNC-ACC-2025-00456",
        "dialysis_type":                  "Peritoneal Dialysis",
        "period_from":                    date(2026, 6, 1),
        "period_to":                      date(2026, 6, 10),
        "number_of_sessions":             6,
        "notes":                "New claim for June 2026. Awaiting physician signature.",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
#  Seed runner
# ─────────────────────────────────────────────────────────────────────────────
def seed():
    init_db()

    with get_db_session() as db:

        # ── 1. Case Rates ─────────────────────────────────────────────────────
        print("\n=== PhilHealth Case Rates ===")
        existing_codes = {r.case_code for r in db.query(PhilHealthRecord).all()}
        rates_added = 0
        for cr in CASE_RATES:
            if cr["case_code"] in existing_codes:
                print(f"  skip  {cr['case_code']} — already exists")
            else:
                db.add(PhilHealthRecord(**cr))
                print(f"  added {cr['case_code']:10}  {cr['case_description'][:45]:<45}  P{cr['case_rate']:>10,.2f}")
                rates_added += 1
        db.flush()

        # ── 2. Patients ───────────────────────────────────────────────────────
        print("\n=== PhilHealth Demo Patients ===")
        existing_pnums = {p.patient_number for p in db.query(Patient).all()}
        patients_added = 0
        for pd in PATIENTS:
            if pd["patient_number"] in existing_pnums:
                print(f"  skip  {pd['patient_number']} — already exists")
            else:
                db.add(Patient(**pd))
                print(f"  added {pd['patient_number']}  {pd['first_name']} {pd['last_name']:<20}  PH#: {pd['philhealth_number']}")
                patients_added += 1
        db.flush()

        # ── 3. Claim Forms ────────────────────────────────────────────────────
        print("\n=== PhilHealth Claim Forms ===")
        existing_forms = {f.form_number for f in db.query(PhilHealthClaimForm).all()}

        # Build patient lookup by patient_number
        patient_map = {p.patient_number: p for p in db.query(Patient).all()}

        forms_added = 0
        for cf in CLAIM_FORMS:
            if cf["form_number"] in existing_forms:
                print(f"  skip  {cf['form_number']} — already exists")
                continue

            patient = patient_map.get(cf["patient_number"])
            if not patient:
                print(f"  [!]  Patient {cf['patient_number']} not found — skipping {cf['form_number']}")
                continue

            payload = {
                "form_number":          cf["form_number"],
                "form_type":            cf["form_type"],
                "status":               cf["status"],
                "patient_id":           patient.id,
                "philhealth_number":    patient.philhealth_number,
                "date_of_claim":        cf.get("date_of_claim", date.today()),
                "diagnosis":            cf.get("diagnosis"),
                "icd_code":             cf.get("icd_code"),
                "case_rate_code":       cf.get("case_rate_code"),
                "total_amount_claimed": cf.get("total_amount_claimed", Decimal("0")),
                "notes":                cf.get("notes"),
                "eclaim_status":        "Pending",
            }

            ft = cf["form_type"]
            if ft in ("CF2", "CF4"):
                payload.update({
                    "admission_date":     cf.get("admission_date"),
                    "discharge_date":     cf.get("discharge_date"),
                    "type_of_admission":  cf.get("type_of_admission", "Ordinary"),
                    "room_charges":       cf.get("room_charges", Decimal("0")),
                    "medicine_charges":   cf.get("medicine_charges", Decimal("0")),
                    "xray_lab_charges":   cf.get("xray_lab_charges", Decimal("0")),
                    "other_charges":      cf.get("other_charges", Decimal("0")),
                    "hospital_share":     cf.get("hospital_share", Decimal("0")),
                })
            elif ft == "CF3":
                payload.update({
                    "physician_name":              cf.get("physician_name"),
                    "physician_prc_no":            cf.get("physician_prc_no"),
                    "physician_ptr_no":            cf.get("physician_ptr_no"),
                    "physician_philhealth_no":     cf.get("physician_philhealth_no"),
                    "type_of_claim":               cf.get("type_of_claim", "Primary"),
                    "professional_fee_claimed":    cf.get("professional_fee_claimed", Decimal("0")),
                    "professional_fee_share":      cf.get("professional_fee_share", Decimal("0")),
                })
            elif ft == "CF5":
                payload.update({
                    "dialysis_center_name":          cf.get("dialysis_center_name"),
                    "dialysis_center_accreditation": cf.get("dialysis_center_accreditation"),
                    "dialysis_type":                 cf.get("dialysis_type", "Hemodialysis"),
                    "period_from":                   cf.get("period_from"),
                    "period_to":                     cf.get("period_to"),
                    "number_of_sessions":            cf.get("number_of_sessions"),
                })

            db.add(PhilHealthClaimForm(**payload))
            print(
                f"  added {cf['form_number']:<28}  {cf['form_type']}  "
                f"{patient.full_name:<22}  [{cf['status']}]"
            )
            forms_added += 1

    print(f"\n{'='*60}")
    print(f"  Case Rates : {rates_added} added")
    print(f"  Patients   : {patients_added} added")
    print(f"  Claim Forms: {forms_added} added  (CF2×2, CF3×2, CF4×2, CF5×2)")
    print(f"{'='*60}")
    print("\nOpen PhilHealth > Claim Forms tab then select any row")
    print("and click  [ View Details ]  to see the full member info.\n")


if __name__ == "__main__":
    seed()
