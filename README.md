# Clinic Management System

A production-ready desktop application for small clinics and medical practices, built with Python, CustomTkinter, and MySQL. Includes patient management, consultations, inventory, billing, PhilHealth benefit computation, and comprehensive reporting.

## Features

- **Multi-user authentication** with role-based access (Administrator, Receptionist, Doctor, Cashier)
- **Patient management** — registration, search, archive, PhilHealth/senior/PWD info
- **Appointments** — scheduling, calendar view, status tracking
- **Consultations** — vital signs, diagnosis, treatment plans, prescriptions
- **Medicine inventory** — stock in/out, batch tracking, expiration alerts
- **Billing** — automatic totals, senior/PWD discounts, partial payments, receipts
- **PhilHealth** — case rate selection, automatic benefit computation, transaction history
- **Reports** — PDF and Excel export for income, patients, inventory, billing, PhilHealth
- **Settings** — clinic info, user management, database backup/restore, audit logs

## Tech Stack

| Layer | Technology |
|-------|------------|
| UI | CustomTkinter |
| Backend | Python 3.10+ |
| Database | MySQL 8.0+ |
| ORM | SQLAlchemy 2.x |
| PDF | ReportLab |
| Excel | OpenPyXL |
| Security | bcrypt password hashing |

## Architecture

```
MVC + Repository + Service Layer

controllers/  → Application orchestration
views/        → CustomTkinter UI
services/     → Business logic
repositories/ → Data access
models/       → SQLAlchemy ORM
```

## Quick Start

### 1. Prerequisites

- Python 3.10 or higher
- MySQL 8.0 or higher
- MySQL client tools (for backup/restore)

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Database

Edit `config/settings.py`:

```python
DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWORD = "your_password"
DB_NAME = "clinic_management"
```

### 4. Create Database

```bash
mysql -u root -p < database/schema.sql
```

### 5. Run Application

```bash
python main.py
```

**Default login:** `admin` / `admin123`

### 6. Seed Sample Data (Optional)

```bash
python -m database.seed_data
```

## Project Structure

```
clinic_management/
├── main.py                 # Entry point
├── config/                 # App configuration & theme
├── controllers/            # MVC controllers
├── models/                 # SQLAlchemy models (19 tables)
├── repositories/           # Data access layer
├── services/               # Business logic
├── views/                  # CustomTkinter UI
│   └── components/         # Reusable widgets
├── reports/                # PDF & Excel generators
├── database/               # Schema, seeder, connection
├── utils/                  # Helpers, security, logging
├── assets/                 # Images, logos
├── logs/                   # Application logs
└── backups/                # Database backups
```

## Roles & Permissions

| Module | Admin | Receptionist | Doctor | Cashier |
|--------|-------|--------------|--------|---------|
| Dashboard | ✓ | ✓ | ✓ | ✓ |
| Patients | ✓ | ✓ | ✓ | ✓ |
| Appointments | ✓ | ✓ | ✓ | — |
| Consultations | ✓ | — | ✓ | — |
| Inventory | ✓ | — | — | — |
| Billing | ✓ | ✓ | — | ✓ |
| PhilHealth | ✓ | — | ✓ | ✓ |
| Reports | ✓ | ✓ | ✓ | ✓ |
| Settings | ✓ | — | — | — |

## PhilHealth Computation

The system computes benefits using configurable case rates:

- **Case Rate Amount** — PhilHealth package rate
- **Hospital Share** — Default 70% of case rate
- **Professional Fee** — Default 30% of case rate
- **PhilHealth Deduction** — Applied against total bill
- **Senior/PWD Discount** — 20% on remaining balance after PhilHealth

> Note: Manual case rate configuration only. No eClaims integration.

## Documentation

- [Installation Guide](docs/INSTALLATION.md)
- [User Manual](docs/USER_MANUAL.md)
- [System Documentation](docs/SYSTEM_DOCUMENTATION.md)

## License

Proprietary — Clinic Management System
