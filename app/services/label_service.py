"""Label-related business logic and validation service."""

from typing import Any

from sqlalchemy.orm import Session

from app.constants import ErrorMessages
from app.exceptions import (
    DuplicateLabelError,
    LabelHierarchyError,
    LabelNotFoundError,
    ValidationError,
)
from app.models.label import Label
from app.repositories.label_repository import LabelRepository


class LabelService:
    """Service for label-related business logic."""

    def __init__(self, session: Session) -> None:
        """Initialize the service with a database session."""
        self.session = session
        self.label_repository = LabelRepository(session)

    def get_label(self, user_id: int, label_id: int) -> Label:
        """
        Get a single label by ID, ensuring user ownership.

        Raises:
            LabelNotFoundError: If label not found or user does not have permission.
        """
        label = self.label_repository.find_by_id(label_id)
        if not label or label.user_id != user_id:
            raise LabelNotFoundError(ErrorMessages.LABEL_NOT_FOUND)
        return label

    def get_labels_by_user(
        self,
        user_id: int,
        parent_id: int | None = None,
    ) -> list[Label]:
        """Get a list of labels for a user."""
        return self.label_repository.find_all_by_user_id(user_id, parent_id)

    def get_label_with_usage(self, user_id: int, label_id: int) -> dict[str, Any]:
        """Get a single label with its usage count."""
        result = self.label_repository.find_by_id_with_usage(label_id)
        if not result or result[0].user_id != user_id:
            raise LabelNotFoundError(ErrorMessages.LABEL_NOT_FOUND)

        label, usage_count = result
        return {
            **label.to_dict(),
            "usage_count": usage_count,
        }  # to_dict()はLabelモデルに要実装

    def get_labels_by_user_with_usage(
        self,
        user_id: int,
        parent_id: int | None = None,
        filter_root_labels: bool = False,
    ) -> list[dict[str, Any]]:
        """Get all labels for a user with their usage counts, optionally filtered by parent_id."""
        if parent_id is not None or filter_root_labels:
            # parent_idが指定されている場合、またはルートレベルのラベルのみを取得する場合
            results = self.label_repository.find_all_by_user_id_with_usage_filtered(
                user_id, parent_id,
            )
        else:
            # parent_idがNoneの場合は、子も含めて全てのラベルを取得
            results = self.label_repository.find_all_by_user_id_with_usage(user_id)
        return [
            {**label.to_dict(), "usage_count": usage_count}
            for label, usage_count in results
        ]  # to_dict()はLabelモデルに要実装

    def create_label(self, user_id: int, data: dict[str, Any]) -> Label:
        """
        Create a new label with validation.

        Raises:
            DuplicateLabelError: If a label with the same name already exists for the user/parent.
            LabelHierarchyError: If hierarchy rules are violated.
            ValidationError: If input data is invalid.
        """
        name = data.get("name")
        parent_id = data.get("parent_id")

        if self.label_repository.find_by_user_and_name_and_parent(
            user_id,
            name,
            parent_id,
        ):
            raise DuplicateLabelError(ErrorMessages.DUPLICATE_LABEL)

        parent = None
        if parent_id:
            parent = self.get_label(user_id, parent_id)

        try:
            label = Label(user_id=user_id, parent=parent, **data)
            label.validate_name()
            label.validate_color()
            label.validate_hierarchy_depth()
        except ValueError as e:
            raise ValidationError(str(e)) from e

        return self.label_repository.save(label)

    def update_label(self, user_id: int, label_id: int, data: dict[str, Any]) -> Label:
        """
        Update an existing label.

        Raises:
            LabelNotFoundError: If the label is not found or user does not have permission.
            DuplicateLabelError: If the new name conflicts with an existing label.
            LabelHierarchyError: If hierarchy rules are violated.
            ValidationError: If update data is invalid.
        """
        label = self.get_label(user_id, label_id)

        if label.system_label:
            raise ValidationError(ErrorMessages.SYSTEM_LABEL_READONLY)

        # 1. 親の変更を先に処理する
        if "parent_id" in data:
            new_parent_id = data["parent_id"]
            if new_parent_id:
                new_parent = self.get_label(user_id, new_parent_id)
                # 循環参照のチェック
                if label.is_ancestor_of(new_parent) or label.label_id == new_parent_id:
                    raise LabelHierarchyError(ErrorMessages.CIRCULAR_REFERENCE)
                # 階層の深さチェック
                if (new_parent.get_depth() + 1 + label.get_subtree_height()) >= 5:
                    raise LabelHierarchyError(ErrorMessages.LABEL_HIERARCHY_TOO_DEEP)

                # オブジェクトとIDの両方を明示的に設定する
                label.parent = new_parent
                label.parent_id = new_parent.label_id
            else:  # parent_id が null の場合
                label.parent = None
                label.parent_id = None

        # 2. 名前の変更を処理する(親が変更された可能性を考慮)
        if "name" in data:
            name = data["name"]
            # 現在の親IDで重複をチェック
            existing = self.label_repository.find_by_user_and_name_and_parent(
                user_id,
                name,
                label.parent_id,
            )
            if existing and existing.label_id != label_id:
                raise DuplicateLabelError(ErrorMessages.DUPLICATE_LABEL)
            label.name = data["name"]

        # 3. 色の変更を処理する
        if "color" in data:
            label.color = data["color"]

        # 4. モデル自身のバリデーションを呼び出す
        try:
            label.validate_name()
            label.validate_color()
        except ValueError as e:
            raise ValidationError(str(e)) from e

        return self.label_repository.save(label)

    def delete_label(self, user_id: int, label_id: int) -> None:
        """
        Delete a label.

        Raises:
            LabelNotFoundError: If the label is not found or user does not have permission.
            ValidationError: If the label cannot be deleted (e.g., system label).
        """
        label = self.get_label(user_id, label_id)

        if not label.can_be_deleted():
            if label.system_label:
                raise ValidationError(ErrorMessages.SYSTEM_LABEL_READONLY)
            raise ValidationError(ErrorMessages.CANNOT_DELETE_LABEL_WITH_CHILDREN)

        self.label_repository.delete(label)
