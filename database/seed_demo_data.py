"""Seed demo patients and billing records for SOA preview showcase."""

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from repositories.billing_repository import BillingRepository
from repositories.patient_repository import PatientRepository
from repositories.philhealth_repository import PhilHealthRepository
from repositories.user_repository import UserRepository
from services.activity_service import ActivityService
from services.billing_service import BillingService
from utils.logger import logger


DEMO_PATIENT_NUMBERS = ("DEMO-PAT-001", "DEMO-PAT-002", "DEMO-PAT-003")
DEMO_PATIENT_NUMBER = DEMO_PATIENT_NUMBERS[0]


def _demo_already_seeded(patient_repo: PatientRepository, billing_repo: BillingRepository) -> bool:
    juan = patient_repo.get_by_patient_number(DEMO_PATIENT_NUMBER)
    if not juan:
        return False
    return bool(billing_repo.get_by_patient(juan.id))


def _ensure_philhealth_rate_fees(rate_repo: PhilHealthRepository, case_code: str):
    rate = rate_repo.get_by_code(case_code)
    if not rate:
        return None
    if not rate.health_facility_fee or not rate.professional_fee_amount:
        amount = Decimal(str(rate.case_rate))
        rate_repo.update(rate, {
            "health_facility_fee": (amount * Decimal("0.70")).quantize(Decimal("0.01")),
            "professional_fee_amount": (amount * Decimal("0.30")).quantize(Decimal("0.01")),
            "case_type": rate.case_type or "Medical",
            "price_effective_date": rate.price_effective_date or date.today(),
        })
    return rate_repo.get_by_code(case_code)


def seed_billing_demo(session: Session) -> None:
    """Create showcase patients and bills if demo data is not present yet."""
    patient_repo = PatientRepository(session)
    billing_repo = BillingRepository(session)
    if _demo_already_seeded(patient_repo, billing_repo):
        return

    user_repo = UserRepository(session)
    admin = user_repo.get_by_username("admin")
    created_by = admin.id if admin else None

    rate_repo = PhilHealthRepository(session)
    billing_service = BillingService(session, ActivityService(session))

    patient_specs = [
        {
            "patient_number": "DEMO-PAT-001",
            "first_name": "Juan",
            "middle_name": "Dela",
            "last_name": "Santos",
            "birth_date": date(1965, 3, 12),
            "gender": "Male",
            "civil_status": "Married",
            "contact_number": "09171234567",
            "address_street": "123 Rizal Street",
            "address_barangay": "Poblacion",
            "address_city": "Quezon City",
            "address_province": "Metro Manila",
            "philhealth_number": "12-345678901-2",
            "philhealth_category": "Indigent",
            "philhealth_member_type": "Member",
            "is_senior_citizen": True,
            "senior_id_number": "SC-2024-00123",
        },
        {
            "patient_number": "DEMO-PAT-002",
            "first_name": "Maria",
            "middle_name": "Luna",
            "last_name": "Cruz",
            "birth_date": date(1988, 7, 22),
            "gender": "Female",
            "civil_status": "Single",
            "contact_number": "09189876543",
            "address_street": "45 Mabini Avenue",
            "address_barangay": "San Roque",
            "address_city": "Makati",
            "address_province": "Metro Manila",
            "philhealth_number": "12-987654321-0",
            "philhealth_category": "Employed in Private Companies",
            "philhealth_member_type": "Member",
        },
        {
            "patient_number": "DEMO-PAT-003",
            "first_name": "Pedro",
            "middle_name": "Garcia",
            "last_name": "Reyes",
            "birth_date": date(1972, 11, 5),
            "gender": "Male",
            "civil_status": "Married",
            "contact_number": "09201112233",
            "address_street": "88 Aguinaldo Highway",
            "address_barangay": "Balagtas",
            "address_city": "Batangas City",
            "address_province": "Batangas",
            "philhealth_number": "12-112233445-5",
            "philhealth_category": "Self-Employed",
            "philhealth_member_type": "Member",
        },
    ]

    created_patients = []
    for data in patient_specs:
        existing = patient_repo.get_by_patient_number(data["patient_number"])
        if existing:
            created_patients.append(existing)
            continue
        data.setdefault("is_archived", False)
        created_patients.append(patient_repo.create(data))

    juan, maria, pedro = created_patients

    uti_rate = _ensure_philhealth_rate_fees(rate_repo, "UTI001")
    pn_rate = _ensure_philhealth_rate_fees(rate_repo, "PN001")
    acr_rate = _ensure_philhealth_rate_fees(rate_repo, "ACR001")

    # Bill 1 — Juan: outpatient UTI package, unpaid (best SOA preview)
    ok, _, bill1 = billing_service.create_billing(juan.id, [
        {"item_type": "Professional Fee", "description": "Physician Consultation - UTI", "quantity": 1, "unit_price": 500},
        {"item_type": "Laboratory", "description": "Complete Blood Count (CBC)", "quantity": 1, "unit_price": 450},
        {"item_type": "Laboratory", "description": "Urinalysis", "quantity": 1, "unit_price": 350},
        {"item_type": "Procedure", "description": "IV Fluid Therapy", "quantity": 1, "unit_price": 1200},
        {"item_type": "Medicine", "description": "Antibiotics & Supplies", "quantity": 1, "unit_price": 1500},
        {"item_type": "Room", "description": "Outpatient Observation (4 hrs)", "quantity": 1, "unit_price": 4500},
    ])
    if ok and bill1 and uti_rate:
        deduction = min(Decimal(str(uti_rate.case_rate)), bill1.subtotal - bill1.discount_amount)
        billing_service.set_philhealth_case_rate(bill1.id, uti_rate.id, deduction)
        billing_service.billing_repo.update(bill1, {
            "notes": "Demo bill for SOA preview - UTI outpatient package",
            "created_by": created_by,
        })

    # Bill 2 — Maria: pneumonia case, partial payment
    ok, _, bill2 = billing_service.create_billing(maria.id, [
        {"item_type": "Professional Fee", "description": "Pulmonology Consultation", "quantity": 1, "unit_price": 800},
        {"item_type": "Laboratory", "description": "Chest X-Ray (PA View)", "quantity": 1, "unit_price": 1200},
        {"item_type": "Procedure", "description": "Nebulization Treatment", "quantity": 3, "unit_price": 350},
        {"item_type": "Medicine", "description": "Antibiotics & Nebulizer Kit", "quantity": 1, "unit_price": 1850},
    ])
    if ok and bill2 and pn_rate:
        deduction = min(Decimal(str(pn_rate.case_rate)), bill2.subtotal - bill2.discount_amount)
        billing_service.set_philhealth_case_rate(bill2.id, pn_rate.id, deduction)
        billing_service.record_payment(bill2.id, Decimal("2000"), "GCash", "Partial demo payment")
        billing_service.billing_repo.update(bill2, {
            "notes": "Demo bill - partial payment showcase",
            "created_by": created_by,
        })

    # Bill 3 — Pedro: gastro case, fully paid
    ok, _, bill3 = billing_service.create_billing(pedro.id, [
        {"item_type": "Professional Fee", "description": "Emergency Consultation", "quantity": 1, "unit_price": 600},
        {"item_type": "Laboratory", "description": "Fecalysis", "quantity": 1, "unit_price": 280},
        {"item_type": "Medicine", "description": "Oral Rehydration & Antiemetics", "quantity": 1, "unit_price": 720},
        {"item_type": "Procedure", "description": "IV Hydration", "quantity": 1, "unit_price": 900},
    ])
    if ok and bill3 and acr_rate:
        deduction = min(Decimal(str(acr_rate.case_rate)), bill3.subtotal - bill3.discount_amount)
        billing_service.set_philhealth_case_rate(bill3.id, acr_rate.id, deduction)
        bill3 = billing_service.get_by_id(bill3.id)
        if bill3 and bill3.balance > 0:
            billing_service.record_payment(bill3.id, bill3.balance, "Cash", "Full demo payment")
        billing_service.billing_repo.update(bill3, {
            "notes": "Demo bill - paid in full showcase",
            "created_by": created_by,
        })

    logger.info(
        "Seeded demo billing data for patients %s, %s, %s.",
        juan.patient_number, maria.patient_number, pedro.patient_number,
    )
