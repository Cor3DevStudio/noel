"""Optional demo data seeder — run after clinic-setup.bat.

Usage:
    python scripts/seed_demo.py
    python scripts/seed_demo.py --accounts-only
    python scripts/seed_demo.py --patients-only
    python scripts/seed_demo.py --philhealth-only
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo data for development.")
    parser.add_argument("--accounts-only", action="store_true")
    parser.add_argument("--patients-only", action="store_true")
    parser.add_argument("--philhealth-only", action="store_true")
    args = parser.parse_args()

    run_all = not (args.accounts_only or args.patients_only or args.philhealth_only)

    if run_all or args.accounts_only:
        print("=== Demo user accounts ===")
        from seed_accounts import seed as seed_accounts

        seed_accounts()

    if run_all or args.patients_only:
        print("\n=== Demo patients ===")
        from seed_patients import seed as seed_patients

        seed_patients()

    if run_all or args.philhealth_only:
        print("\n=== PhilHealth demo data ===")
        from seed_philhealth import seed as seed_philhealth

        seed_philhealth()

    print("\nDemo seed complete.")


if __name__ == "__main__":
    main()
