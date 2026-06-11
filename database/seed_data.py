"""Sample data seeder for development and demo."""

from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from services.auth_service import AuthService
from services.inventory_service import InventoryService
from services.patient_service import PatientService
from utils.security import hash_password


def seed_sample_data(session: Session) -> None:
    auth = AuthService(session)
    auth.initialize_roles()
    auth.create_default_admin()

    roles = {r.name: r.id for r in auth.get_roles()}
    users_data = [
        ("receptionist", "Maria Santos", "Receptionist"),
        ("doctor1", "Dr. Juan Dela Cruz", "Doctor"),
        ("cashier1", "Ana Reyes", "Cashier"),
    ]
    for username, name, role in users_data:
        if not auth.user_repo.get_by_username(username):
            auth.user_repo.create({
                "username": username,
                "password_hash": hash_password("password123"),
                "full_name": name,
                "role_id": roles[role],
                "is_active": True,
            })

    patient_service = PatientService(session)
    patients_data = [
        {
            "first_name": "Pedro", "last_name": "Garcia", "gender": "Male",
            "birth_date": date(1958, 3, 15), "contact_number": "09171234567",
            "philhealth_number": "12-345678901-2", "is_senior_citizen": True,
            "senior_id_number": "SC-12345", "address_city": "Manila",
        },
        {
            "first_name": "Rosa", "last_name": "Mendoza", "gender": "Female",
            "birth_date": date(1985, 7, 22), "contact_number": "09181234567",
            "philhealth_number": "12-987654321-0", "address_city": "Quezon City",
        },
        {
            "first_name": "Jose", "last_name": "Ramos", "gender": "Male",
            "birth_date": date(1970, 11, 8), "contact_number": "09191234567",
            "is_pwd": True, "pwd_id_number": "PWD-78901", "address_city": "Makati",
        },
    ]
    for pdata in patients_data:
        pdata["patient_number"] = patient_service.repo.get_next_number()
        pdata.setdefault("is_archived", False)
        if not patient_service.repo.search(pdata["last_name"]):
            patient_service.repo.create(pdata)

    inventory = InventoryService(session)
    if not inventory.get_categories():
        inventory.add_category("Antibiotics", "Antibacterial medications")
        inventory.add_category("Analgesics", "Pain relief medications")
        inventory.add_category("Vitamins", "Vitamin supplements")

    categories = {c.name: c.id for c in inventory.get_categories()}
    medicines = [
        {"generic_name": "Amoxicillin", "brand_name": "Amoxil", "category_id": categories.get("Antibiotics"),
         "selling_price": 15, "unit_price": 10, "stock_quantity": 100, "expiration_date": date.today() + timedelta(days=365)},
        {"generic_name": "Paracetamol", "brand_name": "Biogesic", "category_id": categories.get("Analgesics"),
         "selling_price": 5, "unit_price": 3, "stock_quantity": 200, "expiration_date": date.today() + timedelta(days=180)},
        {"generic_name": "Metformin", "brand_name": "Glucophage", "category_id": categories.get("Vitamins"),
         "selling_price": 8, "unit_price": 5, "stock_quantity": 5, "expiration_date": date.today() + timedelta(days=60)},
    ]
    for med in medicines:
        if med.get("category_id"):
            existing = inventory.search(med["generic_name"])
            if not existing:
                inventory.add_medicine(med)

    session.commit()
    print("Sample data seeded successfully.")


if __name__ == "__main__":
    from database.connection import SessionLocal, init_db

    init_db()
    db = SessionLocal()
    try:
        seed_sample_data(db)
    finally:
        db.close()
