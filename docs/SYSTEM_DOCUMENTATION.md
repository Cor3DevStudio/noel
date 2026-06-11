# System Documentation

## Overview

The Clinic Management System (CMS) is a desktop application designed for small clinics in the Philippines. It follows MVC architecture with additional Repository and Service layers for maintainability and testability.

## Database Schema

### Entity Relationship Summary

```
users ──► roles
patients ──► appointments, consultations, billings, philhealth_transactions
consultations ──► prescriptions ──► prescription_items
medicines ──► medicine_categories, suppliers, inventory_transactions
billings ──► billing_items, payments
philhealth_records ──► philhealth_transactions
clinic_settings (singleton)
activity_logs, audit_logs
```

### Tables (19)

| Table | Purpose |
|-------|---------|
| roles | Role definitions with JSON permissions |
| users | System users with hashed passwords |
| patients | Patient demographics and PhilHealth info |
| appointments | Scheduled visits |
| consultations | Medical records with JSON vital signs |
| prescriptions | Prescription headers |
| prescription_items | Individual medicine lines |
| medicine_categories | Medicine classification |
| suppliers | Supplier contact info |
| medicines | Medicine master with stock levels |
| inventory_transactions | Stock movement history |
| billings | Billing headers |
| billing_items | Line items per bill |
| payments | Payment records with receipt numbers |
| philhealth_records | Configurable case rates |
| philhealth_transactions | Processed PhilHealth claims |
| clinic_settings | Clinic configuration |
| activity_logs | User activity tracking |
| audit_logs | Data change audit trail |

## Security

- **Password hashing:** bcrypt with per-user salt
- **SQL injection:** SQLAlchemy parameterized queries
- **Role-based access:** Permission checks via `session_manager.has_permission()`
- **Audit trail:** CREATE/UPDATE/DELETE logged with old/new values
- **Activity logging:** Login, logout, and module actions recorded

## PhilHealth Computation Logic

```python
case_rate_amount = selected_case_rate
hospital_share = case_rate_amount × (hospital_share_pct / 100)   # default 70%
professional_fee = case_rate_amount × (professional_fee_pct / 100)  # default 30%
philhealth_deduction = min(case_rate_amount, total_bill)
remaining = total_bill - philhealth_deduction

if patient.is_senior_citizen:
    senior_discount = remaining × 0.20
    remaining -= senior_discount
elif patient.is_pwd:
    pwd_discount = remaining × 0.20
    remaining -= pwd_discount

patient_balance = max(0, remaining)
```

## Billing Logic

```python
subtotal = sum(item.quantity × item.unit_price for item in items)
discount = subtotal × 0.20 if senior or pwd else 0
total = subtotal - discount - philhealth_deduction
balance = total - amount_paid
payment_status = Paid | Partial | Unpaid
```

## Service Layer

| Service | Responsibility |
|---------|---------------|
| AuthService | Login, user CRUD, password management |
| PatientService | Registration, search, archive |
| AppointmentService | Scheduling, status updates |
| ConsultationService | Medical records, prescriptions |
| InventoryService | Stock management, categories |
| BillingService | Bill creation, payments, discounts |
| PhilHealthService | Benefit computation, transactions |
| DashboardService | Aggregated statistics |
| SettingsService | Clinic config, backup/restore |

## Logging

Logs are written to `logs/clinic.log` with rotation (5 MB × 5 files).

Format: `YYYY-MM-DD HH:MM:SS | LEVEL | clinic | message`

## Backup & Restore

Backup uses `mysqldump` to export the full database to `backups/clinic_backup_YYYYMMDD_HHMMSS.sql`.

Restore uses `mysql` CLI to import from a selected `.sql` file.

Both require MySQL client tools in system PATH.

## Configuration

All configuration is in `config/settings.py`:

- Database connection
- UI theme colors
- Discount rates (20% senior/PWD)
- PhilHealth share percentages
- Low stock threshold (10 units)
- Expiry warning days (90 days)
- Role permissions map

## Extension Points

- Add new case rates via Settings or PhilHealth module
- Custom report types in `reports/report_generator.py`
- Additional roles via `ROLE_PERMISSIONS` in settings
- PDF templates in `reports/pdf_generator.py`
