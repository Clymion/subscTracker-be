"""Repository for label data access logic."""

from sqlalchemy import func
from sqlalchemy.orm import Session, aliased

from app.models.association_tables import subscription_labels
from app.models.label import Label


class LabelRepository:
    """Repository for label data access logic."""

    def __init__(self, session: Session) -> None:
        """
        Initialize the repository with a database session.

        Args:
            session: The SQLAlchemy Session object.
        """
        self.session = session

    def find_by_id(self, label_id: int) -> Label | None:
        """Find a label by its ID."""
        return self.session.get(Label, label_id)

    def find_by_id_with_usage(self, label_id: int) -> tuple[Label, int] | None:
        """Find a label by ID and include its usage count."""
        result = (
            self.session.query(Label, func.count(subscription_labels.c.subscription_id))
            .outerjoin(subscription_labels)
            .filter(Label.label_id == label_id)
            .group_by(Label.label_id)
            .first()
        )
        return result if result else None

    def find_by_user_and_name_and_parent(
        self, user_id: int, name: str, parent_id: int | None,
    ) -> Label | None:
        """Find a label by user, name (case-insensitive), and parent."""
        return (
            self.session.query(Label)
            .filter(
                Label.user_id == user_id,
                Label.parent_id == parent_id,
                func.lower(Label.name) == func.lower(name),
            )
            .first()
        )

    def find_all_by_user_id(
        self, user_id: int, parent_id: int | None = None,
    ) -> list[Label]:
        """Find all labels for a user, optionally filtered by parent."""
        query = self.session.query(Label).filter_by(user_id=user_id)
        if parent_id is not None:
            query = query.filter_by(parent_id=parent_id)
        # 階層構造と名前でソート
        return query.order_by(Label.parent_id.is_(None).desc(), Label.name).all()

    def find_all_by_user_id_with_usage(self, user_id: int) -> list[tuple[Label, int]]:
        """Find all user labels and include their usage counts."""
        return (
            self.session.query(Label, func.count(subscription_labels.c.subscription_id))
            .outerjoin(subscription_labels)
            .filter(Label.user_id == user_id)
            .group_by(Label.label_id)
            .order_by(Label.parent_id.is_(None).desc(), Label.name)
            .all()
        )

    def save(self, label: Label) -> Label:
        """Save a label (create or update)."""
        self.session.add(label)
        self.session.commit()
        self.session.refresh(label)
        return label

    def delete(self, label: Label) -> None:
        """Delete a label."""
        self.session.delete(label)
        self.session.commit()
