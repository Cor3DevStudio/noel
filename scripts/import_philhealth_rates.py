"""
Import PhilHealth Case Rates from official PDF annexes into the database.

Usage:
    python scripts/import_philhealth_rates.py

PDFs expected at:
    C:/Users/Karl/Downloads/AnnexA-ListofMedicalCaseRates.pdf   (Medical, ICD codes)
    C:/Users/Karl/Downloads/AnnexB-ListofProcedureCaseRates.pdf  (Surgical, RVS codes)

Populates the philhealth_records table.  Safe to re-run (upserts by case_code).
"""

from datetime import date
import re
import sys
from pathlib import Path
from typing import Generator

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pdfplumber

from database.connection import SessionLocal
from models.philhealth import PhilHealthRecord

# ── Paths ──────────────────────────────────────────────────────────────────────
ANNEX_A_PATH = r"C:/Users/Karl/Downloads/AnnexA-ListofMedicalCaseRates.pdf"
ANNEX_B_PATH = r"C:/Users/Karl/Downloads/AnnexB-ListofProcedureCaseRates.pdf"

# ── Helpers ────────────────────────────────────────────────────────────────────

SKIP_CELLS = re.compile(
    r"^(ICD Code|RVS Code|Description|First Case Rate|Case Rate|"
    r"Health Facility Fee|Professional Fee|Page \d+|Annex [AB])$",
    re.IGNORECASE,
)

AMT_RE = re.compile(r"[\d\s,]+\.\d{2}")


def parse_amount(s: str) -> float:
    """Parse '1 9,500.00' → 19500.0 (removes interior spaces)."""
    if not s:
        return 0.0
    cleaned = s.replace(" ", "").replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def is_skip(val) -> bool:
    if val is None:
        return True
    v = str(val).strip()
    return not v or SKIP_CELLS.match(v) is not None


def extract_rows(pdf_path: str, case_type: str) -> Generator[dict, None, None]:
    """
    Yield {code, description, case_rate, health_facility_fee, professional_fee}
    for every valid data row in the PDF table.
    """
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if not row or len(row) < 3:
                        continue
                    code = (row[0] or "").strip()
                    desc = (row[1] or "").strip()
                    cr   = (row[2] or "").strip()
                    hff  = (row[3] or "").strip() if len(row) > 3 else ""
                    pf   = (row[4] or "").strip() if len(row) > 4 else ""

                    # Skip header / footer rows
                    if is_skip(code) or not code or not cr:
                        continue
                    if not AMT_RE.match(cr.replace(" ", "").replace(",", "")):
                        continue
                    if len(code) > 20:
                        continue

                    cr_val  = parse_amount(cr)
                    hff_val = parse_amount(hff) if hff else round(cr_val * 0.70, 2)
                    pf_val  = parse_amount(pf)  if pf  else round(cr_val * 0.30, 2)

                    if cr_val <= 0:
                        continue

                    yield {
                        "code":                code,
                        "description":         desc[:255],
                        "case_rate":           cr_val,
                        "health_facility_fee": hff_val,
                        "professional_fee":    pf_val,
                        "case_type":           case_type,
                    }


# ── Database upsert ────────────────────────────────────────────────────────────

def import_rates(records: list) -> tuple[int, int]:
    session = SessionLocal()
    inserted = updated = 0
    try:
        for rec in records:
            existing = (
                session.query(PhilHealthRecord)
                .filter_by(case_code=rec["code"])
                .first()
            )
            if existing:
                price_changed = (
                    existing.case_rate != rec["case_rate"]
                    or existing.health_facility_fee != rec["health_facility_fee"]
                    or existing.professional_fee_amount != rec["professional_fee"]
                )
                existing.case_description       = rec["description"]
                existing.case_rate              = rec["case_rate"]
                existing.health_facility_fee    = rec["health_facility_fee"]
                existing.professional_fee_amount = rec["professional_fee"]
                existing.case_type              = rec["case_type"]
                existing.hospital_share_pct     = 70.0
                existing.professional_fee_pct   = 30.0
                existing.is_active              = True
                if price_changed:
                    existing.price_effective_date = date.today()
                updated += 1
            else:
                session.add(PhilHealthRecord(
                    case_code              = rec["code"],
                    case_description       = rec["description"],
                    case_rate              = rec["case_rate"],
                    health_facility_fee    = rec["health_facility_fee"],
                    professional_fee_amount = rec["professional_fee"],
                    case_type              = rec["case_type"],
                    hospital_share_pct     = 70.0,
                    professional_fee_pct   = 30.0,
                    is_active              = True,
                    price_effective_date   = date.today(),
                ))
                inserted += 1
            if (inserted + updated) % 500 == 0:
                session.flush()
                print(f"    ... {inserted + updated} processed")
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
    return inserted, updated


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 62)
    print("PhilHealth Case Rates Import")
    print("=" * 62)

    for path, label, case_type in [
        (ANNEX_A_PATH, "Annex A – Medical Case Rates (ICD-10)",      "Medical"),
        (ANNEX_B_PATH, "Annex B – Surgical Procedure Rates (RVS)",   "Surgical"),
    ]:
        if not Path(path).exists():
            print(f"[SKIP] File not found: {path}")
            continue

        print(f"\n[{label}]")
        print("  Reading PDF and extracting table rows ...")
        raw = list(extract_rows(path, case_type))
        # Deduplicate — keep first occurrence of each code
        seen: set[str] = set()
        records = []
        for r in raw:
            if r["code"] not in seen:
                seen.add(r["code"])
                records.append(r)
        print(f"  Parsed {len(raw)} rows, {len(records)} unique codes")

        if not records:
            print("  [!] No records found - skipping.")
            continue

        print("  Inserting / updating in database …")
        ins, upd = import_rates(records)
        print(f"  Done: {ins} inserted,  {upd} updated")

    print("\n[COMPLETE] PhilHealth case rates import finished.")


if __name__ == "__main__":
    main()
