"""Seed PhilHealth case rates (pricelist) from bundled data or official PDF annexes."""

from __future__ import annotations

import gzip
import json
import re
from datetime import date
from pathlib import Path
from typing import Generator, Iterable

from sqlalchemy.orm import Session

from config.settings import BASE_DIR, ECLAIMS_DIR
from models.philhealth import PhilHealthRecord
from utils.logger import logger

RATES_BUNDLE = Path(__file__).resolve().parent / "philhealth_rates.json.gz"
MIN_EXPECTED_RATES = 1000
BATCH_SIZE = 500

SKIP_CELLS = re.compile(
    r"^(ICD Code|RVS Code|Description|First Case Rate|Case Rate|"
    r"Health Facility Fee|Professional Fee|Page \d+|Annex [AB])$",
    re.IGNORECASE,
)
AMT_RE = re.compile(r"[\d\s,]+\.\d{2}")

DEFAULT_RATES = [
    {"case_code": "ACR001", "case_description": "Acute Gastroenteritis", "case_rate": 6000},
    {"case_code": "PN001", "case_description": "Community Acquired Pneumonia", "case_rate": 15000},
    {"case_code": "UTI001", "case_description": "Urinary Tract Infection", "case_rate": 6000},
    {"case_code": "HTN001", "case_description": "Hypertension Package", "case_rate": 9000},
    {"case_code": "DM001", "case_description": "Diabetes Mellitus Package", "case_rate": 9000},
]

ANNEX_CANDIDATES = (
    (
        "AnnexA-ListofMedicalCaseRates.pdf",
        "Annex A – Medical Case Rates (ICD-10)",
        "Medical",
    ),
    (
        "AnnexB-ListofProcedureCaseRates.pdf",
        "Annex B – Surgical Procedure Rates (RVS)",
        "Surgical",
    ),
)


def _rate_count(session: Session) -> int:
    return session.query(PhilHealthRecord).count()


def _resolve_annex_path(filename: str) -> Path | None:
    for folder in (ECLAIMS_DIR, BASE_DIR / "assets" / "philhealth", Path.home() / "Downloads"):
        path = folder / filename
        if path.exists():
            return path
    return None


def parse_amount(value: str) -> float:
    if not value:
        return 0.0
    cleaned = value.replace(" ", "").replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def is_skip(value) -> bool:
    if value is None:
        return True
    text = str(value).strip()
    return not text or SKIP_CELLS.match(text) is not None


def extract_rows_from_pdf(pdf_path: Path, case_type: str) -> Generator[dict, None, None]:
    import pdfplumber

    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables() or []:
                for row in table:
                    if not row or len(row) < 3:
                        continue
                    code = (row[0] or "").strip()
                    desc = (row[1] or "").strip()
                    case_rate = (row[2] or "").strip()
                    hff = (row[3] or "").strip() if len(row) > 3 else ""
                    pf = (row[4] or "").strip() if len(row) > 4 else ""

                    if is_skip(code) or not code or not case_rate:
                        continue
                    if not AMT_RE.match(case_rate.replace(" ", "").replace(",", "")):
                        continue
                    if len(code) > 20:
                        continue

                    case_rate_val = parse_amount(case_rate)
                    if case_rate_val <= 0:
                        continue

                    hff_val = parse_amount(hff) if hff else round(case_rate_val * 0.70, 2)
                    pf_val = parse_amount(pf) if pf else round(case_rate_val * 0.30, 2)

                    yield {
                        "case_code": code,
                        "case_description": desc[:255],
                        "case_rate": case_rate_val,
                        "health_facility_fee": hff_val,
                        "professional_fee_amount": pf_val,
                        "case_type": case_type,
                        "hospital_share_pct": 70.0,
                        "professional_fee_pct": 30.0,
                        "is_active": True,
                    }


def load_bundle_records() -> list[dict]:
    if not RATES_BUNDLE.exists():
        return []
    with gzip.open(RATES_BUNDLE, "rt", encoding="utf-8") as handle:
        data = json.load(handle)
    return data if isinstance(data, list) else []


def load_pdf_records() -> list[dict]:
    records: list[dict] = []
    seen: set[str] = set()

    for filename, _label, case_type in ANNEX_CANDIDATES:
        path = _resolve_annex_path(filename)
        if path is None:
            continue
        for row in extract_rows_from_pdf(path, case_type):
            code = row["case_code"]
            if code in seen:
                continue
            seen.add(code)
            records.append(row)
    return records


def _normalize_record(record: dict) -> dict:
    case_rate = float(record.get("case_rate") or 0)
    hff = record.get("health_facility_fee")
    pf = record.get("professional_fee_amount")
    return {
        "case_code": str(record["case_code"]).strip(),
        "case_description": str(record.get("case_description") or "")[:255],
        "case_type": record.get("case_type") or "Medical",
        "case_rate": case_rate,
        "health_facility_fee": float(hff if hff is not None else round(case_rate * 0.70, 2)),
        "professional_fee_amount": float(pf if pf is not None else round(case_rate * 0.30, 2)),
        "hospital_share_pct": float(record.get("hospital_share_pct") or 70.0),
        "professional_fee_pct": float(record.get("professional_fee_pct") or 30.0),
        "is_active": bool(record.get("is_active", True)),
    }


def upsert_rates(session: Session, records: Iterable[dict]) -> tuple[int, int]:
    inserted = updated = 0
    today = date.today()

    for record in records:
        data = _normalize_record(record)
        existing = (
            session.query(PhilHealthRecord)
            .filter_by(case_code=data["case_code"])
            .first()
        )
        if existing:
            price_changed = (
                float(existing.case_rate) != data["case_rate"]
                or float(existing.health_facility_fee) != data["health_facility_fee"]
                or float(existing.professional_fee_amount) != data["professional_fee_amount"]
            )
            existing.case_description = data["case_description"]
            existing.case_rate = data["case_rate"]
            existing.health_facility_fee = data["health_facility_fee"]
            existing.professional_fee_amount = data["professional_fee_amount"]
            existing.case_type = data["case_type"]
            existing.hospital_share_pct = data["hospital_share_pct"]
            existing.professional_fee_pct = data["professional_fee_pct"]
            existing.is_active = data["is_active"]
            if price_changed:
                existing.price_effective_date = today
            updated += 1
        else:
            session.add(PhilHealthRecord(
                case_code=data["case_code"],
                case_description=data["case_description"],
                case_rate=data["case_rate"],
                health_facility_fee=data["health_facility_fee"],
                professional_fee_amount=data["professional_fee_amount"],
                case_type=data["case_type"],
                hospital_share_pct=data["hospital_share_pct"],
                professional_fee_pct=data["professional_fee_pct"],
                is_active=data["is_active"],
                price_effective_date=today,
            ))
            inserted += 1

        if (inserted + updated) % BATCH_SIZE == 0:
            session.flush()

    return inserted, updated


def seed_default_rates(session: Session) -> None:
    for record in DEFAULT_RATES:
        if session.query(PhilHealthRecord).filter_by(case_code=record["case_code"]).first():
            continue
        case_rate = float(record["case_rate"])
        session.add(PhilHealthRecord(
            case_code=record["case_code"],
            case_description=record["case_description"],
            case_rate=case_rate,
            health_facility_fee=round(case_rate * 0.70, 2),
            professional_fee_amount=round(case_rate * 0.30, 2),
            case_type="Medical",
            hospital_share_pct=70.0,
            professional_fee_pct=30.0,
            is_active=True,
            price_effective_date=date.today(),
        ))


def ensure_philhealth_rates(session: Session) -> None:
    """Load full PhilHealth pricelist when the database has too few case rates."""
    current = _rate_count(session)
    if current >= MIN_EXPECTED_RATES:
        return

    source = ""
    records: list[dict] = []

    bundle_records = load_bundle_records()
    if bundle_records:
        source = str(RATES_BUNDLE.name)
        records = bundle_records
    else:
        try:
            pdf_records = load_pdf_records()
        except ImportError:
            pdf_records = []
        if pdf_records:
            source = "PhilHealth PDF annexes"
            records = pdf_records

    if records:
        logger.info(
            "Loading PhilHealth pricelist from %s (%s records)...",
            source,
            len(records),
        )
        inserted, updated = upsert_rates(session, records)
        session.flush()
        logger.info(
            "PhilHealth pricelist ready: %s inserted, %s updated (total now %s).",
            inserted,
            updated,
            _rate_count(session),
        )
        return

    if current == 0:
        seed_default_rates(session)
        session.flush()
        logger.warning(
            "PhilHealth pricelist bundle not found; seeded %s default case rates only.",
            len(DEFAULT_RATES),
        )
