from typing import Any

from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from app.models.payment_history import PaymentHistory


class PaymentHistoryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def find_by_id(self, payment_id: int) -> PaymentHistory | None:
        return self.session.query(PaymentHistory).filter_by(payment_id=payment_id).first()

    def _apply_filters(self, query: Any, filters: dict[str, Any]) -> Any:
        if filters.get("subscription_id") is not None:
            query = query.filter(PaymentHistory.subscription_id == filters["subscription_id"])
        if filters.get("start_date") is not None:
            query = query.filter(PaymentHistory.payment_date >= filters["start_date"])
        if filters.get("end_date") is not None:
            query = query.filter(PaymentHistory.payment_date <= filters["end_date"])
        if filters.get("currency") is not None:
            query = query.filter(PaymentHistory.currency == filters["currency"])
        if filters.get("payment_method") is not None:
            query = query.filter(PaymentHistory.payment_method == filters["payment_method"])
        return query

    def find_all_by_user_id(
        self,
        user_id: int,
        filters: dict[str, Any],
        sort_by: str,
        sort_order: str,
        limit: int,
        offset: int,
    ) -> list[PaymentHistory]:
        query = self.session.query(PaymentHistory).filter(PaymentHistory.user_id == user_id)
        query = self._apply_filters(query, filters)

        sort_column = getattr(PaymentHistory, sort_by, PaymentHistory.payment_date)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        return query.limit(limit).offset(offset).all()

    def count_all_by_user_id(self, user_id: int, filters: dict[str, Any]) -> int:
        query = self.session.query(PaymentHistory.payment_id).filter(PaymentHistory.user_id == user_id)
        query = self._apply_filters(query, filters)
        return query.count()

    def save(self, payment_history: PaymentHistory) -> PaymentHistory:
        self.session.add(payment_history)
        self.session.commit()
        self.session.refresh(payment_history)
        return payment_history

    def delete(self, payment_history: PaymentHistory) -> None:
        self.session.delete(payment_history)
        self.session.commit()
