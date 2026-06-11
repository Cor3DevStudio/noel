"""Setup script: create database, tables, migrations, and seed default data."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from controllers.app_controller import AppController
from utils.logger import logger


def main() -> int:
    print("Setting up clinic database...")
    controller = None
    try:
        controller = AppController()
        controller.initialize_database()
        print("Database setup complete.")
        print("  - Tables created (if missing)")
        print("  - Schema migrations applied")
        print("  - Seed accounts, rates, and demo billing inserted (if missing)")
        return 0
    except Exception as exc:
        print(f"Database setup failed: {exc}")
        logger.error("Clinic setup failed: %s", exc)
        print()
        print("Check that MySQL is running and config/settings.py is correct.")
        return 1
    finally:
        if controller:
            controller.close()


if __name__ == "__main__":
    sys.exit(main())
