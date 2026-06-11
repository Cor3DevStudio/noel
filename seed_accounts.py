"""Seed script — inserts one demo user account per clinic role."""

import sys

sys.path.insert(0, ".")

from database.connection import get_db_session, init_db
from repositories.user_repository import RoleRepository, UserRepository
from services.auth_service import AuthService
from utils.security import hash_password


ACCOUNTS = [
    {
        "username":   "admin",
        "password":   "admin123",
        "full_name":  "System Administrator",
        "email":      "admin@clinic.local",
        "role_name":  "Administrator",
        "is_active":  True,
    },
    {
        "username":   "dr.reyes",
        "password":   "doctor123",
        "full_name":  "Dr. Maria Reyes",
        "email":      "dr.reyes@clinic.local",
        "role_name":  "Doctor",
        "is_active":  True,
    },
    {
        "username":   "dr.santos",
        "password":   "doctor123",
        "full_name":  "Dr. Jose Santos",
        "email":      "dr.santos@clinic.local",
        "role_name":  "Doctor",
        "is_active":  True,
    },
    {
        "username":   "receptionist",
        "password":   "recep123",
        "full_name":  "Ana Bautista",
        "email":      "receptionist@clinic.local",
        "role_name":  "Receptionist",
        "is_active":  True,
    },
    {
        "username":   "cashier",
        "password":   "cashier123",
        "full_name":  "Carlos Lim",
        "email":      "cashier@clinic.local",
        "role_name":  "Cashier",
        "is_active":  True,
    },
]


def seed():
    init_db()
    inserted = 0
    skipped = 0

    with get_db_session() as db:
        AuthService(db).initialize_roles()
        user_repo = UserRepository(db)
        role_repo = RoleRepository(db)

        roles = {r.name: r for r in role_repo.get_all()}

        for acct in ACCOUNTS:
            role_name = acct["role_name"]
            role = roles.get(role_name)
            if role is None:
                print(f"  [!] Role '{role_name}' not found — skipping {acct['username']}")
                skipped += 1
                continue

            if user_repo.get_by_username(acct["username"]):
                print(f"  skip  {acct['username']} ({role_name}) — already exists")
                skipped += 1
                continue

            user_repo.create({
                "role_id":       role.id,
                "username":      acct["username"],
                "password_hash": hash_password(acct["password"]),
                "full_name":     acct["full_name"],
                "email":         acct["email"],
                "is_active":     acct["is_active"],
            })
            print(f"  added {acct['username']:<20} ({role_name:<14})  pw: {acct['password']}")
            inserted += 1

    print(f"\nDone — {inserted} inserted, {skipped} skipped.")
    print("\n== Seeded credentials ==================================")
    print(f"  {'Username':<20} {'Role':<16} {'Password'}")
    print(f"  {'-'*20} {'-'*16} {'-'*12}")
    for a in ACCOUNTS:
        print(f"  {a['username']:<20} {a['role_name']:<16} {a['password']}")
    print("=========================================================")


if __name__ == "__main__":
    seed()
