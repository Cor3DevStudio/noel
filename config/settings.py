"""Application configuration and theme settings."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
LOGS_DIR = BASE_DIR / "logs"
BACKUP_DIR = BASE_DIR / "backups"
UPLOADS_DIR = BASE_DIR / "uploads"

ECLAIMS_DIR = BASE_DIR / "eclaims"

for directory in (ASSETS_DIR, LOGS_DIR, BACKUP_DIR, UPLOADS_DIR, ECLAIMS_DIR):
    directory.mkdir(parents=True, exist_ok=True)

# Database
DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWORD = ""  # Leave empty if MySQL has no password
DB_NAME = "clinic_management"

if DB_PASSWORD:
    DATABASE_URL = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    )
else:
    DATABASE_URL = f"mysql+pymysql://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# Application
APP_NAME = "Hospital Management System"
APP_VERSION = "1.0.0"
SCHEMA_VERSION = 2
SCHEMA_VERSION_FILE = BASE_DIR / ".db_schema_version"

# Page refresh cache (seconds) — skip redundant DB reloads when revisiting a tab
VIEW_REFRESH_TTL_SEC = 20
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"

# UI Theme - Minimalist Medical Professional
THEME = {
    "primary": "#FFFFFF",
    "secondary": "#F8F9FA",
    "accent": "#2563EB",
    "accent_hover": "#1D4ED8",
    "text_primary": "#1E293B",
    "text_secondary": "#64748B",
    "text_muted": "#94A3B8",
    "border": "#E2E8F0",
    "success": "#10B981",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "sidebar_bg": "#1E293B",
    "sidebar_text": "#F8FAFC",
    "sidebar_hover": "#334155",
    "card_bg": "#FFFFFF",
    "card_shadow": "#E2E8F0",
}

# Discount rates
SENIOR_DISCOUNT_RATE = 0.20
PWD_DISCOUNT_RATE = 0.20

# PhilHealth default shares (percentage)
PHILHEALTH_HOSPITAL_SHARE = 0.70
PHILHEALTH_PROFESSIONAL_SHARE = 0.30

# Inventory alerts
LOW_STOCK_THRESHOLD = 10
EXPIRY_WARNING_DAYS = 90

# Roles
ROLES = ["Administrator", "Receptionist", "Doctor", "Cashier"]

PAGE_PERMISSIONS = [
    ("dashboard", "Dashboard"),
    ("patients", "Patients"),
    ("appointments", "Appointments"),
    ("consultations", "Consultations"),
    ("inventory", "Inventory"),
    ("billing", "Billing"),
    ("philhealth", "PhilHealth"),
    ("pricelist", "Price List"),
    ("reports", "Reports"),
    ("settings", "Settings"),
]

ROLE_PERMISSIONS = {
    "Administrator": [
        "dashboard", "patients", "appointments", "consultations",
        "prescriptions", "inventory", "billing", "philhealth",
        "pricelist", "reports", "settings", "users",
    ],
    "Receptionist": [
        "dashboard", "patients", "appointments", "billing",
        "pricelist", "reports",
    ],
    "Doctor": [
        "dashboard", "patients", "appointments", "consultations",
        "prescriptions", "philhealth", "pricelist", "reports",
    ],
    "Cashier": [
        "dashboard", "patients", "billing", "philhealth",
        "pricelist", "reports",
    ],
}
