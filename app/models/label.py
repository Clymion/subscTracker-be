"""
Label model for organizing subscriptions with hierarchical structure.

This module defines the Label SQLAlchemy model with hierarchy support,
color validation, and business logic methods for label management.
"""

import re
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.constants import ErrorMessages, LabelConstants
from app.models import db


class Label(db.Model):
    """
    Label model for organizing subscriptions with hierarchical structure.

    This model supports nested categories (parent-child relationships),
    color coding, and system vs user-defined labels.
    """

    __tablename__ = "labels"

    # Primary key
    label_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # Foreign key to users table
    user_id: Mapped[int] = mapped_column(
        Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Parent-child relationship (self-referential)
    parent_id: Mapped[int | None] = mapped_column(
        Integer,
        db.ForeignKey("labels.label_id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Basic label information
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False)  # Hex color #FFFFFF
    system_label: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        # User + Parent composite index for hierarchical queries
        Index("idx_labels_user_parent", "user_id", "parent_id"),
    )

    # Relationships
    user = relationship("User", back_populates="labels")
    parent = relationship("Label", remote_side=[label_id], back_populates="children")
    children = relationship(
        "Label",
        back_populates="parent",
        cascade="all, delete-orphan",
        lazy="select",
    )
    subscriptions = relationship(
        "Subscription",
        secondary="subscription_labels",
        back_populates="labels",
        lazy="select",
    )

    def __init__(self, **kwargs) -> None:
        """Initialize a new Label instance with validation."""
        super().__init__(**kwargs)
        if self.system_label is None:
            self.system_label = False

    def __repr__(self) -> str:
        """String representation of the label."""
        return f"<Label {self.name} ({self.color})>"

    def __str__(self) -> str:
        """Human-readable string representation."""
        return self.name

    # Validation methods
    def validate_name(self) -> None:
        """Validate that name is provided and not too long."""
        if not self.name or not self.name.strip():
            raise ValueError(ErrorMessages.LABEL_NAME_REQUIRED)

        if len(self.name.strip()) > 100:
            raise ValueError(ErrorMessages.LABEL_NAME_TOO_LONG)

    def validate_color(self) -> None:
        """Validate that color is in valid hex format."""
        if not self.color:
            raise ValueError(ErrorMessages.LABEL_COLOR_REQUIRED)

        # Normalize color format (#fff -> #FFFFFF)
        self.color = self._normalize_color(self.color)

        # Validate hex format
        if not self._is_valid_hex_color(self.color):
            raise ValueError(ErrorMessages.INVALID_HEX_COLOR)

    def validate_hierarchy_depth(self) -> None:
        """Validate that hierarchy doesn't exceed maximum depth."""
        depth = self.get_depth()
        if depth >= LabelConstants.MAX_HIERARCHY_DEPTH:
            raise ValueError(ErrorMessages.LABEL_HIERARCHY_TOO_DEEP)

    def validate_no_circular_reference(
        self,
        new_parent_id: int | None = None,
    ) -> None:
        """Validate that setting parent doesn't create circular reference."""
        if new_parent_id is None:
            new_parent_id = self.parent_id

        if new_parent_id is None:
            return  # No parent, no circular reference possible

        if new_parent_id == self.label_id:
            raise ValueError(ErrorMessages.CIRCULAR_REFERENCE)

        # Check if new parent is a descendant
        descendants = self.get_descendants()
        if any(desc.label_id == new_parent_id for desc in descendants):
            raise ValueError(ErrorMessages.CIRCULAR_REFERENCE)

    # Business logic methods
    def calculate_usage_count(self) -> int:
        """Calculate real-time usage count from subscription relationships."""
        return len(self.subscriptions) if self.subscriptions else 0

    def is_used(self) -> bool:
        """Check if label is currently used by any subscriptions."""
        return self.calculate_usage_count() > 0

    def can_be_deleted(self) -> bool:
        """Check if label can be deleted (not system label and no children)."""
        if self.system_label:
            return False
        return len(self.children) == 0

    def get_depth(self) -> int:
        """Get hierarchy depth level (0 for root labels)."""
        depth = 0
        current_parent = self.parent
        while current_parent is not None:
            depth += 1
            current_parent = current_parent.parent
            if depth > LabelConstants.MAX_HIERARCHY_DEPTH:
                break  # Safety check to prevent infinite loops
        return depth

    def get_full_path(self) -> str:
        """Get hierarchical path (e.g., 'Parent > Child > Grandchild')."""
        ancestors = self.get_ancestors()
        ancestors.reverse()  # Reverse to get root first
        ancestors.append(self)
        return " > ".join(label.name for label in ancestors)

    def get_ancestors(self) -> list["Label"]:
        """Get all parent labels up the hierarchy."""
        ancestors = []
        current_parent = self.parent
        while current_parent is not None:
            ancestors.append(current_parent)
            current_parent = current_parent.parent
            if len(ancestors) > LabelConstants.MAX_HIERARCHY_DEPTH:
                break  # Safety check
        return ancestors

    def get_descendants(self) -> list["Label"]:
        """Get all child labels down the hierarchy."""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants

    def is_ancestor_of(self, other_label: "Label") -> bool:
        """Check if this label is an ancestor of another label."""
        return self in other_label.get_ancestors()

    # Private utility methods
    def _normalize_color(self, color: str) -> str:
        """Normalize color to uppercase 6-character hex format."""
        if not color:
            return color

        color = color.strip().upper()

        # Add # if missing
        if not color.startswith("#"):
            color = f"#{color}"

        # Expand 3-character hex to 6-character
        if len(color) == 4:  # #RGB -> #RRGGBB
            color = f"#{color[1]}{color[1]}{color[2]}{color[2]}{color[3]}{color[3]}"

        return color

    def _is_valid_hex_color(self, color: str) -> bool:
        """Check if color is valid hex format."""
        if not color:
            return False

        # Should be #RRGGBB format
        pattern = r"^#[0-9A-F]{6}$"
        return bool(re.match(pattern, color))
