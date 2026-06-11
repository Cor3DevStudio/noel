from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from models.philhealth import PhilHealthRecord, PhilHealthTransaction
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
