"""Seed script — inserts 10 test patients with PhilHealth data."""

import sys
from datetime import date

# Make sure project root is on path
sys.path.insert(0, ".")

from database.connection import get_db_session, init_db
from models.patient import Patient


PATIENTS = [
    {
        "patient_number":        "P-2026-001",
        "first_name":            "Maria",
        "middle_name":           "Santos",
        "last_name":             "Reyes",
        "birth_date":            date(1985, 3, 14),
        "gender":                "Female",
        "civil_status":          "Married",
        "contact_number":        "09171234501",
        "address_street":        "123 Rizal St.",
        "address_barangay":      "Barangay 1",
        "address_city":          "Manila",
        "address_province":      "Metro Manila",
        "philhealth_number":     "04-123456789-0",
        "philhealth_category":   "Employed",
        "philhealth_member_type":"Member",
        "is_senior_citizen":     False,
        "is_pwd":                False,
    },
    {
        "patient_number":        "P-2026-002",
        "first_name":            "Jose",
        "middle_name":           "Cruz",
        "last_name":             "Dela Torre",
        "birth_date":            date(1948, 7, 22),
        "gender":                "Male",
        "civil_status":          "Widowed",
        "contact_number":        "09181234502",
        "address_street":        "456 Mabini Ave.",
        "address_barangay":      "Barangay 5",
        "address_city":          "Quezon City",
        "address_province":      "Metro Manila",
        "philhealth_number":     "04-234567890-1",
        "philhealth_category":   "Senior Citizen",
        "philhealth_member_type":"Dependent",
        "is_senior_citizen":     True,
        "senior_id_number":      "SC-2024-00123",
        "is_pwd":                False,
    },
    {
        "patient_number":        "P-2026-003",
        "first_name":            "Ana",
        "middle_name":           "Bautista",
        "last_name":             "Garcia",
        "birth_date":            date(1992, 11, 5),
        "gender":                "Female",
        "civil_status":          "Single",
        "contact_number":        "09191234503",
        "address_street":        "789 Bonifacio Blvd.",
        "address_barangay":      "Barangay 10",
        "address_city":          "Pasig",
        "address_province":      "Metro Manila",
        "philhealth_number":     "04-345678901-2",
        "philhealth_category":   "Indigent",
        "philhealth_member_type":"Member",
        "is_senior_citizen":     False,
        "is_pwd":                True,
        "pwd_id_number":         "PWD-2023-00456",
    },
    {
        "patient_number":        "P-2026-004",
        "first_name":            "Carlos",
        "middle_name":           "Mendoza",
        "last_name":             "Lim",
        "birth_date":            date(1978, 1, 30),
        "gender":                "Male",
        "civil_status":          "Married",
        "contact_number":        "09201234504",
        "address_street":        "22 Luna St.",
        "address_barangay":      "Barangay 3",
        "address_city":          "Makati",
        "address_province":      "Metro Manila",
        "philhealth_number":     "04-456789012-3",
        "philhealth_category":   "Self-Employed",
        "philhealth_member_type":"Member",
        "is_senior_citizen":     False,
        "is_pwd":                False,
    },
    {
        "patient_number":        "P-2026-005",
        "first_name":            "Rosa",
        "middle_name":           "Flores",
        "last_name":             "Villanueva",
        "birth_date":            date(1965, 6, 18),
        "gender":                "Female",
        "civil_status":          "Separated",
        "contact_number":        "09211234505",
        "address_street":        "55 Aguinaldo St.",
        "address_barangay":      "Barangay 7",
        "address_city":          "Caloocan",
        "address_province":      "Metro Manila",
        "philhealth_number":     "04-567890123-4",
        "philhealth_category":   "Employed",
        "philhealth_member_type":"Dependent",
        "is_senior_citizen":     False,
        "is_pwd":                False,
    },
    {
        "patient_number":        "P-2026-006",
        "first_name":            "Ramon",
        "middle_name":           None,
        "last_name":             "Aquino",
        "birth_date":            date(1950, 9, 3),
        "gender":                "Male",
        "civil_status":          "Married",
        "contact_number":        "09221234506",
        "address_street":        "88 Magsaysay Rd.",
        "address_barangay":      "Barangay 12",
        "address_city":          "Taguig",
        "address_province":      "Metro Manila",
        "philhealth_number":     "04-678901234-5",
        "philhealth_category":   "Senior Citizen",
        "philhealth_member_type":"Member",
        "is_senior_citizen":     True,
        "senior_id_number":      "SC-2023-00789",
        "is_pwd":                False,
    },
    {
        "patient_number":        "P-2026-007",
        "first_name":            "Lina",
        "middle_name":           "Torres",
        "last_name":             "Castillo",
        "birth_date":            date(2000, 4, 25),
        "gender":                "Female",
        "civil_status":          "Single",
        "contact_number":        "09231234507",
        "address_street":        "10 Lapu-Lapu St.",
        "address_barangay":      "Barangay 2",
        "address_city":          "Mandaluyong",
        "address_province":      "Metro Manila",
        "philhealth_number":     "04-789012345-6",
        "philhealth_category":   "Employed",
        "philhealth_member_type":"Member",
        "is_senior_citizen":     False,
        "is_pwd":                False,
    },
    {
        "patient_number":        "P-2026-008",
        "first_name":            "Eduardo",
        "middle_name":           "Ramos",
        "last_name":             "Pascual",
        "birth_date":            date(1955, 12, 10),
        "gender":                "Male",
        "civil_status":          "Married",
        "contact_number":        "09241234508",
        "address_street":        "33 Andres Bonifacio St.",
        "address_barangay":      "Barangay 8",
        "address_city":          "Valenzuela",
        "address_province":      "Metro Manila",
        "philhealth_number":     "04-890123456-7",
        "philhealth_category":   "Retired",
        "philhealth_member_type":"Member",
        "is_senior_citizen":     True,
        "senior_id_number":      "SC-2022-00321",
        "is_pwd":                False,
    },
    {
        "patient_number":        "P-2026-009",
        "first_name":            "Cristina",
        "middle_name":           "Navarro",
        "last_name":             "Hernandez",
        "birth_date":            date(1988, 8, 16),
        "gender":                "Female",
        "civil_status":          "Married",
        "contact_number":        "09251234509",
        "address_street":        "77 Roxas Blvd.",
        "address_barangay":      "Barangay 4",
        "address_city":          "Paranaque",
        "address_province":      "Metro Manila",
        "philhealth_number":     "04-901234567-8",
        "philhealth_category":   "OFW",
        "philhealth_member_type":"Member",
        "is_senior_citizen":     False,
        "is_pwd":                False,
    },
    {
        "patient_number":        "P-2026-010",
        "first_name":            "Miguel",
        "middle_name":           "Padilla",
        "last_name":             "Fernandez",
        "birth_date":            date(1972, 2, 28),
        "gender":                "Male",
        "civil_status":          "Single",
        "contact_number":        "09261234510",
        "address_street":        "66 Del Pilar St.",
        "address_barangay":      "Barangay 6",
        "address_city":          "Las Pinas",
        "address_province":      "Metro Manila",
        "philhealth_number":     "04-012345678-9",
        "philhealth_category":   "Self-Employed",
        "philhealth_member_type":"Member",
        "is_senior_citizen":     False,
        "is_pwd":                True,
        "pwd_id_number":         "PWD-2024-00789",
    },
]


def seed():
    init_db()
    inserted = 0
    skipped = 0

    with get_db_session() as db:
        existing_numbers = {
            p.patient_number
            for p in db.query(Patient.patient_number).all()  # type: ignore[arg-type]
        }

        for data in PATIENTS:
            if data["patient_number"] in existing_numbers:
                print(f"  skip  {data['patient_number']} — already exists")
                skipped += 1
                continue

            patient = Patient(**data)
            db.add(patient)
            print(f"  added {data['patient_number']}  {data['first_name']} {data['last_name']}")
            inserted += 1

    print(f"\nDone — {inserted} inserted, {skipped} skipped.")


if __name__ == "__main__":
    seed()
