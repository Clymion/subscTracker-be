from typing import Any

from sqlalchemy.orm import Session

from app.repositories.payment_history_repository import PaymentHistoryRepository


class PaymentHistoryService:
    def __init__(self, session: Session, payment_history_repository: PaymentHistoryRepository | None = None) -> None:
        self.session = session
        self.payment_history_repository = payment_history_repository or PaymentHistoryRepository(session)

    def get_payment_history(
        self,
        user_id: int,
        filters: dict[str, Any],
        sort_by: str,
        sort_order: str,
        limit: int,
        offset: int,
    ) -> tuple[list[Any], int]:
        payments = self.payment_history_repository.find_all_by_user_id(
            user_id,
            filters,
            sort_by,
            sort_order,
            limit,
            offset,
        )
        total = self.payment_history_repository.count_all_by_user_id(user_id, filters)
        return payments, total
