from typing import List, Optional, Tuple

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from models.philhealth import PhilHealthClaimForm, PhilHealthRecord, PhilHealthTransaction
from repositories.base_repository import BaseRepository


class PhilHealthRepository(BaseRepository[PhilHealthRecord]):
    def __init__(self, session: Session) -> None:
        super().__init__(PhilHealthRecord, session)

    def get_active_rates(self) -> List[PhilHealthRecord]:
        return (
            self.session.query(PhilHealthRecord)
            .filter(PhilHealthRecord.is_active == True)
            .order_by(PhilHealthRecord.case_code)
            .all()
        )

    def get_by_code(self, case_code: str) -> Optional[PhilHealthRecord]:
        return (
            self.session.query(PhilHealthRecord)
            .filter(PhilHealthRecord.case_code == case_code)
            .first()
        )

    def search(
        self,
        query: str = "",
        case_type: str = "All",
        page: int = 1,
        per_page: int = 50,
    ) -> Tuple[List[PhilHealthRecord], int]:
        """Return (records, total_count) with optional search + type filter + pagination."""
        q = self.session.query(PhilHealthRecord)
        if case_type != "All":
            q = q.filter(PhilHealthRecord.case_type == case_type)
        if query.strip():
            like = f"%{query.strip()}%"
            q = q.filter(
                or_(
                    PhilHealthRecord.case_code.ilike(like),
                    PhilHealthRecord.case_description.ilike(like),
                )
            )
        total = q.with_entities(func.count(PhilHealthRecord.id)).scalar()
        records = (
            q.order_by(PhilHealthRecord.case_code)
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return records, total

    def get_type_counts(self) -> dict:
        rows = (
            self.session.query(PhilHealthRecord.case_type, func.count(PhilHealthRecord.id))
            .group_by(PhilHealthRecord.case_type)
            .all()
        )
        counts = {"Medical": 0, "Surgical": 0}
        for case_type, cnt in rows:
            if case_type in counts:
                counts[case_type] = cnt
        return counts


class PhilHealthTransactionRepository(BaseRepository[PhilHealthTransaction]):
    def __init__(self, session: Session) -> None:
        super().__init__(PhilHealthTransaction, session)

    def get_by_patient(self, patient_id: int) -> List[PhilHealthTransaction]:
        return (
            self.session.query(PhilHealthTransaction)
            .options(joinedload(PhilHealthTransaction.case_rate))
            .filter(PhilHealthTransaction.patient_id == patient_id)
            .order_by(PhilHealthTransaction.transaction_date.desc())
            .all()
        )


class PhilHealthClaimFormRepository(BaseRepository[PhilHealthClaimForm]):
    def __init__(self, session: Session) -> None:
        super().__init__(PhilHealthClaimForm, session)

    def get_by_patient(self, patient_id: int) -> List[PhilHealthClaimForm]:
        return (
            self.session.query(PhilHealthClaimForm)
            .filter(PhilHealthClaimForm.patient_id == patient_id)
            .order_by(PhilHealthClaimForm.created_at.desc())
            .all()
        )

    def get_active_claim_for_patient(self, patient_id: int) -> Optional[PhilHealthClaimForm]:
        """Return the latest Draft claim, or latest Pending eClaim form for the patient."""
        forms = self.get_by_patient(patient_id)
        for form in forms:
            if form.status == "Draft":
                return form
        for form in forms:
            if getattr(form, "eclaim_status", "Pending") == "Pending":
                return form
        return forms[0] if forms else None

    def get_by_form_type(self, form_type: str) -> List[PhilHealthClaimForm]:
        return (
            self.session.query(PhilHealthClaimForm)
            .filter(PhilHealthClaimForm.form_type == form_type)
            .order_by(PhilHealthClaimForm.created_at.desc())
            .all()
        )

    def get_by_number(self, form_number: str) -> Optional[PhilHealthClaimForm]:
        return (
            self.session.query(PhilHealthClaimForm)
            .filter(PhilHealthClaimForm.form_number == form_number)
            .first()
        )

    def get_all(self) -> List[PhilHealthClaimForm]:
        return (
            self.session.query(PhilHealthClaimForm)
            .options(joinedload(PhilHealthClaimForm.patient))
            .order_by(PhilHealthClaimForm.created_at.desc())
            .all()
        )
